from cms.models import Placeholder
from cms.plugin_rendering import BaseRenderer
from cms.utils.conf import get_cms_setting
from cms.utils.plugins import get_plugins
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.shortcuts import get_current_site
from django.db import models
from django.urls import reverse
from rest_framework import serializers
from rest_framework.request import Request

from djangocms_rest.serializers.cache_utils import get_placeholder_rest_cache, set_placeholder_rest_cache
from djangocms_rest.serializers.utils import render_html, render_plugin


class PlaceholderRenderer(BaseRenderer):
    """
    The `PlaceholderRenderer` class is a custom renderer that renders a placeholder object.
    """

    def placeholder_cache_is_enabled(self):
        if not get_cms_setting("PLACEHOLDER_CACHE"):
            return False
        if self.request.user.is_staff:
            return False
        # return True
        # breaks fetching the placeholder content, caching implementation is not working as expected
        # Reduce complexity and replace API caching with redis caching
        return False

    def render_placeholder(self, placeholder, context, language, use_cache=False):
        context.update({"request": self.request})
        if use_cache and placeholder.cache_placeholder:
            use_cache = self.placeholder_cache_is_enabled()
        else:
            use_cache = False

        if use_cache:
            cached_value = get_placeholder_rest_cache(
                placeholder,
                lang=language,
                site_id=get_current_site(self.request).pk,
                request=self.request,
            )
        else:
            cached_value = None

        if cached_value is not None:
            # User has opted to use the cache
            # and there is something in the cache
            return cached_value["content"]

        plugin_content = self.render_plugins(
            placeholder,
            language=language,
            context=context,
        )

        if use_cache:
            set_placeholder_rest_cache(
                placeholder,
                lang=language,
                site_id=get_current_site(self.request).pk,
                content=plugin_content,
                request=self.request,
            )

        if placeholder.pk not in self._rendered_placeholders:
            # First time this placeholder is rendered
            self._rendered_placeholders[placeholder.pk] = plugin_content

        return plugin_content

    def render_plugins(self, placeholder: Placeholder, language: str, context: dict) -> list:
        plugins = get_plugins(
            self.request,
            placeholder=placeholder,
            lang=language,
            template=None,
        )

        def render_children(child_plugins):
            for plugin in child_plugins:
                plugin_content = render_plugin(plugin, context)
                if getattr(plugin, "child_plugin_instances", None):
                    plugin_content["children"] = render_children(plugin.child_plugin_instances)
                if plugin_content:
                    yield plugin_content

        return list(render_children(plugins))


class PlaceholderSerializer(serializers.Serializer):
    slot = serializers.CharField()
    label = serializers.CharField()
    language = serializers.CharField()
    content = serializers.ListSerializer(child=serializers.JSONField(), allow_empty=True, required=False)

    def __init__(self, request: Request, placeholder: Placeholder, language: str, *args, **kwargs):
        renderer = PlaceholderRenderer(request)
        placeholder.content = renderer.render_placeholder(
            placeholder,
            context={},
            language=language,
            use_cache=True,
        )
        if request.GET.get("html", False):
            html = render_html(request, placeholder, language)
            for key, value in html.items():
                if not hasattr(placeholder, key):
                    setattr(placeholder, key, value)
                    self.fields[key] = serializers.CharField()
        placeholder.label = placeholder.get_label()
        placeholder.language = language
        super().__init__(placeholder, *args, **kwargs)


class PlaceholderRelationFieldSerializer(serializers.Serializer):
    def __init__(self, request: Request, instance: models.Model, placeholders, language: str, *args, **kwargs) -> None:
        self.placeholders = placeholders
        self.language: str = language
        super().__init__(instance, *args, **kwargs)
        self.host: str = f"{request.scheme}://{request.get_host()}"

        for placeholder in self.placeholders:
            self.fields[placeholder.slot] = serializers.JSONField()

    def to_representation(self, instance):
        content_type_id = ContentType.objects.get_for_model(instance.__class__).pk

        return (
            {
                placeholder.slot: self.host
                + reverse(
                    "cms-placeholder-detail",
                    args=(
                        self.language,
                        content_type_id,
                        instance.pk,
                        placeholder.slot,
                    ),
                )
                for placeholder in self.placeholders
            }
            if instance
            else {}
        )


class PlaceholderRelationSerializer(serializers.Serializer):
    content_type_id = serializers.IntegerField()
    object_id = serializers.IntegerField()
    slot = serializers.CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = self.context.get("request")
