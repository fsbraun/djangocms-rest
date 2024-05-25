import datetime

from cms.models import PageContent
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework import serializers
from rest_framework.request import Request


class RESTPage:
    def __init__(
        self, request: Request, page_content: PageContent
    ) -> None:
        host = f"{request.scheme}://{request.get_host()}"
        self.title: str = page_content.title
        self.page_title: str = page_content.page_title or self.title
        self.menu_title: str = page_content.menu_title or self.title
        self.meta_description: str = page_content.meta_description
        self.redirect: str = page_content.redirect
        placeholders = page_content.page.get_placeholders(page_content.language)
        declared_slots = [
            placeholder.slot for placeholder in page_content.page.get_declared_placeholders()
        ]
        content_type_id = ContentType.objects.get_for_model(
            page_content.__class__
        ).pk
        self.placeholders: dict[str, str] = (
            {
                placeholder.slot: host
                + reverse(
                    "placeholder-detail",
                    args=(
                        page_content.language,
                        content_type_id,
                        page_content.pk,
                        placeholder.slot,
                    ),
                )
                for placeholder in placeholders
                if placeholder.slot in declared_slots
            }
            if page_content
            else {}
        )
        self.in_navigation: bool = page_content.in_navigation
        self.soft_root: bool = page_content.soft_root
        self.template: str = page_content.template
        self.xframe_options: str = page_content.xframe_options
        self.limit_visibility_in_menu: int = page_content.limit_visibility_in_menu
        self.language: str = page_content.language

        self.absolute_url: str = page_content.page.get_absolute_url(page_content.language)
        self.path: str = page_content.page.get_path(page_content.language)

        self.is_home: bool = page_content.page.is_home
        self.languages: list[str] = page_content.page.languages.split(",")
        super().__init__()


class PageSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    page_title = serializers.CharField(max_length=255)
    menu_title = serializers.CharField(max_length=255)
    meta_description = serializers.CharField()
    redirect = serializers.CharField(max_length=2048)
    absolute_url = serializers.URLField(max_length=200)

    placeholders = serializers.DictField()
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
