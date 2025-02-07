from typing import Dict

from cms.models import PageContent
from django.db import models
from rest_framework import serializers

from djangocms_rest.serializers.placeholder import PlaceholderRelationSerializer


class BasePageSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    page_title = serializers.CharField(max_length=255)
    menu_title = serializers.CharField(max_length=255)
    meta_description = serializers.CharField()
    redirect = serializers.CharField(max_length=2048)
    absolute_url = serializers.URLField(max_length=200)
    placeholders: PlaceholderRelationSerializer()
    path = serializers.CharField(max_length=200)
    is_home = serializers.BooleanField()
    in_navigation = serializers.BooleanField()
    soft_root = serializers.BooleanField()
    template = serializers.CharField(max_length=100)
    xframe_options = serializers.CharField(max_length=50)
    limit_visibility_in_menu = serializers.BooleanField()
    language = serializers.CharField(max_length=10)
    languages = serializers.ListSerializer(child=serializers.CharField(), allow_empty=True, required=False)


class PageTreeSerializer(serializers.ListSerializer):
    def __init__(self, tree: Dict, *args, **kwargs):
        if not isinstance(tree, dict):
            raise TypeError(f"Expected tree to be a dict, got {type(tree).__name__}")
        self.tree = tree
        super().__init__(tree.get(None, []), *args, **kwargs)

    def tree_to_representation(self, item: PageContent) -> Dict:
        serialized_data = self.child.to_representation(item)
        if item.page.node in self.tree:
            serialized_data["children"] = [self.tree_to_representation(child) for child in self.tree[item.page.node]]
        return serialized_data

    def to_representation(self, data: Dict) -> list[Dict]:
        nodes = data.all() if isinstance(data, models.manager.BaseManager) else data
        return [self.tree_to_representation(node) for node in nodes]


class PageMetaSerializer(BasePageSerializer):
    children = serializers.ListSerializer(child=serializers.DictField(), required=False, default=[])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = self.context.get("request")

    @classmethod
    def many_init(cls, *args, **kwargs):
        """
        Build a tree from the instances if `as_tree` is True.
        """
        context = kwargs.get("context", {})
        if args:
            instances = list(args[0])
        else:
            instances = []
        tree = {}
        for instance in instances:
            parent = instance.page.node.parent
            tree.setdefault(parent, []).append(instance)

        # Prepare the child serializer with proper context.
        kwargs["child"] = cls(context=context)
        return PageTreeSerializer(tree, context=context, *args[1:], **kwargs)

    def to_representation(self, page_content: PageContent) -> Dict:
        relative_url = page_content.page.get_absolute_url(page_content.language)

        return {
            "title": page_content.title,
            "page_title": page_content.page_title or page_content.title,
            "menu_title": page_content.menu_title or page_content.title,
            "meta_description": page_content.meta_description,
            "redirect": page_content.redirect,
            "in_navigation": page_content.in_navigation,
            "soft_root": page_content.soft_root,
            "template": page_content.template,
            "xframe_options": page_content.xframe_options,
            "limit_visibility_in_menu": page_content.limit_visibility_in_menu,
            "language": page_content.language,
            "path": relative_url,
            "is_home": page_content.page.is_home,
            "languages": page_content.page.languages.split(","),
        }


class PageContentSerializer(BasePageSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = self.context.get("request")

    def to_representation(self, page_content: PageContent) -> Dict:
        declared_slots = [placeholder.slot for placeholder in page_content.page.get_declared_placeholders()]
        placeholders = [
            placeholder
            for placeholder in page_content.page.get_placeholders(page_content.language)
            if placeholder.slot in declared_slots
        ]

        placeholders_data = [
            {
                "content_type_id": placeholder.content_type_id,
                "object_id": placeholder.object_id,
                "slot": placeholder.slot,
            }
            for placeholder in placeholders
        ]

        relative_url = page_content.page.get_absolute_url(page_content.language)

        return {
            "title": page_content.title,
            "page_title": page_content.page_title or page_content.title,
            "menu_title": page_content.menu_title or page_content.title,
            "meta_description": page_content.meta_description,
            "redirect": page_content.redirect,
            "placeholders": PlaceholderRelationSerializer(placeholders_data, many=True).data,
            "in_navigation": page_content.in_navigation,
            "soft_root": page_content.soft_root,
            "template": page_content.template,
            "xframe_options": page_content.xframe_options,
            "limit_visibility_in_menu": page_content.limit_visibility_in_menu,
            "language": page_content.language,
            "path": relative_url,
            "is_home": page_content.page.is_home,
            "languages": page_content.page.languages.split(","),
        }
