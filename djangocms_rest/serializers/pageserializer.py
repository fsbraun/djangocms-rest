from django.db import models
from django.urls import reverse
from rest_framework import serializers
from rest_framework.request import Request

from djangocms_rest.serializers.placeholder import PlaceholderRelationFieldSerializer


class PageTreeSerializer(serializers.ListSerializer):
    def __init__(self, tree, *args, **kwargs):
        self.tree = tree
        super().__init__(tree.get(None, []), *args, **kwargs)

    def tree_to_representation(self, item):
        repr = self.child.to_representation(item)
        if item.page.node in self.tree:
            repr["children"] = [
                self.tree_to_representation(child) for child in self.tree[item.page.node]
            ]
        return repr

    def to_representation(self, data):
        """
        List of object instances -> List of dicts of primitive datatypes.
        """
        # Dealing with nested relationships, data can be a Manager,
        # so, first get a queryset from the Manager if needed
        iterable = data.all() if isinstance(data, models.manager.BaseManager) else data

        return [
            self.tree_to_representation(item) for item in iterable
        ]


class PageContentSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    page_title = serializers.CharField(max_length=255)
    menu_title = serializers.CharField(max_length=255)
    meta_description = serializers.CharField()
    redirect = serializers.CharField(max_length=2048)
    absolute_url = serializers.URLField(max_length=200)

    placeholders = serializers.JSONField()
    path = serializers.CharField(max_length=200)

    is_home = serializers.BooleanField()
    in_navigation = serializers.BooleanField()
    soft_root = serializers.BooleanField()
    template = serializers.CharField(max_length=100)
    xframe_options = serializers.CharField(max_length=50)
    limit_visibility_in_menu = serializers.BooleanField()

    language = serializers.CharField(max_length=10)
    languages = serializers.ListSerializer(
        child=serializers.CharField(), allow_empty=True, required=False
    )

    def __init__(self, request: Request, *args, **kwargs) -> None:
        self.request = request
        super().__init__(*args, **kwargs)

    @classmethod
    def many_init(cls, request, instances, *args, **kwargs):
        kwargs['child'] = cls(request)
        if kwargs.pop("as_tree", True):
            tree = {}
            for instance in instances:
                if instance.page.node.parent in tree:
                    tree[instance.page.node.parent].append(instance)
                else:
                    tree[instance.page.node.parent] = [instance]
            return PageTreeSerializer(tree, *args, **kwargs)
        return serializers.ListSerializer(instances, *args, **kwargs)

    def to_representation(self, page_content):
        declared_slots = [
            placeholder.slot
            for placeholder in page_content.page.get_declared_placeholders()
        ]
        placeholders = [
            placeholder
            for placeholder in page_content.page.get_placeholders(page_content.language)
            if placeholder.slot in declared_slots
        ]

        return {
            "title": page_content.title,
            "page_title": page_content.page_title or page_content.title,
            "menu_title": page_content.menu_title or page_content.title,
            "meta_description": page_content.meta_description,
            "redirect": page_content.redirect,
            "placeholders": PlaceholderRelationFieldSerializer(
                self.request,
                page_content,
                placeholders,
                page_content.language,
            ).data,
            "in_navigation": page_content.in_navigation,
            "soft_root": page_content.soft_root,
            "template": page_content.template,
            "xframe_options": page_content.xframe_options,
            "limit_visibility_in_menu": page_content.limit_visibility_in_menu,
            "language": page_content.language,
            "absolute_url": page_content.page.get_absolute_url(
                page_content.language
            ),
            "path": f"{self.request.scheme}://{self.request.get_host()}" + reverse(
                "cms-page-root",
                args=(page_content.language,)
            ) if page_content.page.is_home else f"{self.request.scheme}://{self.request.get_host()}" + reverse(
                "cms-page-detail",
                args=(page_content.language, page_content.page.get_path(page_content.language),)
            ),
            "is_home": page_content.page.is_home,
            "languages": page_content.page.languages.split(","),
        }
