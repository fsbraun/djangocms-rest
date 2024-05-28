import time

from cms.cache.placeholder import (
    _get_placeholder_cache_key,
    _get_placeholder_cache_version_key,
)
from cms.models import Placeholder
from cms.plugin_rendering import BaseRenderer, ContentRenderer
from cms.utils.conf import get_cms_setting
from cms.utils.plugins import get_plugins
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.shortcuts import get_current_site
from django.db import models
from django.template.defaulttags import now
from django.urls import reverse
from rest_framework import serializers
from rest_framework.request import Request
from sekizai.context import SekizaiContext
from sekizai.helpers import get_varname


def _get_placeholder_cache_version(placeholder, lang, site_id):
    """
    Gets the (placeholder x lang)'s current version and vary-on header-names
    list, if present, otherwise resets to («timestamp», []).
    """
    from django.core.cache import cache

    key = _get_placeholder_cache_version_key(placeholder, lang, site_id) + ":rest"
    cached = cache.get(key)
    if cached:
        version, vary_on_list = cached
    else:
        version = int(time.time() * 1000000)
        vary_on_list = []
        _set_placeholder_cache_version(
            placeholder, lang, site_id, version, vary_on_list
        )
    return version, vary_on_list


def _set_placeholder_cache_version(
    placeholder, lang, site_id, version, vary_on_list=None, duration=None
):
    """
    Sets the (placeholder x lang)'s version and vary-on header-names list.
    """
    from django.core.cache import cache

    key = _get_placeholder_cache_version_key(placeholder, lang, site_id) + ":rest"

    if not version or version < 1:
        version = int(time.time() * 1000000)

    if vary_on_list is None:
        vary_on_list = []

    cache.set(key, (version, vary_on_list), duration)


def set_placeholder_rest_cache(placeholder, lang, site_id, content, request):
    """
    Sets the (correct) placeholder cache with the rendered placeholder.
    """
    from django.core.cache import cache

    key = _get_placeholder_cache_key(placeholder, lang, site_id, request) + ":rest"

    duration = min(
        get_cms_setting("CACHE_DURATIONS")["content"],
        placeholder.get_cache_expiration(request, now()),
    )
    cache.set(key, content, duration)
    # "touch" the cache-version, so that it stays as fresh as this content.
    version, vary_on_list = _get_placeholder_cache_version(placeholder, lang, site_id)
    _set_placeholder_cache_version(
        placeholder, lang, site_id, version, vary_on_list, duration=duration
    )


def get_placeholder_rest_cache(placeholder, lang, site_id, request):
    """
    Returns the placeholder from cache respecting the placeholder's
    VARY headers.
    """
    from django.core.cache import cache

    key = (
        _get_placeholder_cache_key(placeholder, lang, site_id, request, soft=True)
        + ":rest"
    )
    content = cache.get(key)
    return content


class PlaceholderRenderer(BaseRenderer):
    """
    The `PlaceholderRenderer` class is a custom renderer that renders a placeholder object.
    """

    def placeholder_cache_is_enabled(self):
        if not get_cms_setting("PLACEHOLDER_CACHE"):
            return False
        if self.request.user.is_staff:
            return False
        return True

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

    def render_plugins(
        self, placeholder: Placeholder, language: str, context: dict
    ) -> list:
        plugins = get_plugins(
            self.request,
            placeholder=placeholder,
            lang=language,
            template=None,
        )

        def render_children(plugins):
            for plugin in plugins:
                plugin_content = self.render_plugin(plugin, context)
                if getattr(plugin, "child_plugin_instances", None):
                    plugin_content["children"] = render_children(
                        plugin.child_plugin_instances
                    )
                if plugin_content:
                    yield plugin_content

        return list(render_children(plugins))

    def render_plugin(self, instance, context):
        instance, plugin = instance.get_plugin_instance()
        if not instance:
            return None
        if hasattr(instance, "serializer") and issubclass(
            instance.serializer, serializers.Serializer
        ):
            json = instance.serializer(instance, context=context).data
        if hasattr(instance, "serialize"):
            json = instance.serialize(context=context)

        class PluginSerializer(serializers.ModelSerializer):
            class Meta:
                model = instance.__class__
                exclude = (
                    "id",
                    "placeholder",
                    "language",
                    "position",
                    "creation_date",
                    "changed_date",
                    "parent",
                )

        json = PluginSerializer(instance, context=context).data
        return json


class PlaceholderSerializer(serializers.Serializer):
    slot = serializers.CharField()
    label = serializers.CharField()
    language = serializers.CharField()
    content = serializers.ListSerializer(
        child=serializers.JSONField(), allow_empty=True, required=False
    )

    def __init__(
        self, request: Request, placeholder: Placeholder, language: str, *args, **kwargs
    ):
        renderer = PlaceholderRenderer(request)
        placeholder.content = renderer.render_placeholder(
            placeholder,
            context={},
            language=language,
            use_cache=True,
        )
        if request.GET.get("html", False):
            html = self.render_html(request, placeholder, language)
            for key, value in html.items():
                if not hasattr(placeholder, key):
                    setattr(placeholder, key, value)
                    self.fields[key] = serializers.CharField()
        placeholder.label = placeholder.get_label()
        placeholder.language = language
        super().__init__(placeholder, *args, **kwargs)

    def render_html(self, request, placeholder, language):
        content_renderer = ContentRenderer(request)
        context = SekizaiContext({"request": request, "LANGUAGE_CODE": language})
        content = content_renderer.render_placeholder(
            placeholder,
            context=context,
            language=language,
            use_cache=True,
        )
        sekizai_blocks = context[get_varname()]

        return {
            "html": content,
            **{key: "".join(value) for key, value in sekizai_blocks.items() if value},
        }


class PlaceholderRelationFieldSerializer(serializers.Serializer):
    def __init__(self, request: Request, instance: models.Model, placeholders, language: str, *args, **kwargs) -> None:
        self.placeholders = placeholders
        self.language: str = language
        super().__init__(instance,*args, **kwargs)
        self.host: str = f"{request.scheme}://{request.get_host()}"

        for placeholder in self.placeholders:
            self.fields[placeholder.slot] = serializers.JSONField()

    def to_representation(self, instance):
        content_type_id = ContentType.objects.get_for_model(
            instance.__class__
        ).pk

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
