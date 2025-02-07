from cms.models import Page, PageContent
from cms.utils.conf import get_languages
from cms.utils.i18n import get_language_tuple
from cms.utils.page_permissions import user_can_view_page
from django.contrib.sites.shortcuts import get_current_site
from django.http import Http404
from django.urls import reverse
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView as DRFAPIView

from djangocms_rest.serializers.language_serializers import LanguageSerializer
from djangocms_rest.serializers.pageserializer import PageContentSerializer, PageMetaSerializer
from djangocms_rest.serializers.placeholder import PlaceholderSerializer
from djangocms_rest.utils import get_object, get_placeholder


class APIView(DRFAPIView):
    # This is a base class for all API views. It sets the allowed methods to GET and OPTIONS.
    http_method_names = ("get", "options")


class LanguageList(APIView):
    """
    List of languages available for the site. For each language the API returns the
    link to the list of pages for that languages.
    """

    @extend_schema(
        responses={200: LanguageSerializer},
    )
    def get(self, request: Request) -> Response:
        languages = get_languages().get(get_current_site(request).id, None)
        if languages is None:
            raise Http404
        for conf in languages:
            conf["pages"] = f"{request.scheme}://{request.get_host()}" + reverse("cms-page-list", args=(conf["code"],))
        serializer = LanguageSerializer(languages, many=True)
        return Response(serializer.data)


class PageTreeList(APIView):
    """
    List of all pages on this site for a given language.
    """

    @extend_schema(
        responses=PageMetaSerializer, description="Get a list of all pages for the given language on the current site."
    )
    def get(self, request, language):
        site = get_current_site(request)
        allowed_languages = [lang[0] for lang in get_language_tuple(site.id)]
        if language not in allowed_languages:
            raise Http404
        qs = Page.objects.filter(node__site=site)
        if request.user.is_anonymous:
            qs = qs.filter(login_required=False)
        pages = (
            page.get_content_obj(language, fallback=True)
            for page in qs
            if user_can_view_page(request.user, page) and page.get_content_obj(language, fallback=True)
        )
        serializer = PageMetaSerializer(
            pages,
            many=True,
            read_only=True,
        )
        return Response(serializer.data)


class PageDetail(APIView):
    """
    Retrieve a page instance. The page instance includes the placeholders and
    their links to retrieve dynamic content.
    """

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="language",
                type=str,
                location=OpenApiParameter.PATH,
                description="Language code (e.g. 'en' or 'de')",
            ),
            OpenApiParameter(
                name="path",
                type=str,
                location=OpenApiParameter.PATH,
                required=False,
                description="Optional page path. If omitted, the home page is returned.",
            ),
        ],
        responses=PageContentSerializer,
        description="Get a page instance with placeholders and their links to retrieve dynamic content.",
    )
    def get(self, request: Request, language: str, path: str = "") -> Response:
        site = get_current_site(request)
        allowed_languages = [lang[0] for lang in get_language_tuple(site.pk)]
        if language not in allowed_languages:
            raise Http404

        page = get_object(site, path)

        if not user_can_view_page(request.user, page):
            raise Http404

        page_content = page.get_content_obj(language, fallback=True)
        serializer = PageContentSerializer(page_content, read_only=True)
        try:
            data = serializer.data
        except PageContent.DoesNotExist:
            raise Http404
        return Response(data)


class PlaceholderDetail(APIView):
    """Placeholder contain the dynamic content. This view retrieves the content as a
    structured nested object.

    Attributes:

    - "slot": The slot name of the placeholder.
    - "content": The content of the placeholder as a nested JSON tree
    - "language": The language of the content
    - "label": The verbose label of the placeholder

    Optional (if the get parameter `?html=1` is added to the API url):
    - "html": The content rendered as html. Sekizai blocks such as "js" or "css" will be added
      as separate attributes"""

    def get(self, request: Request, language: str, content_type_id: int, object_id: int, slot: str) -> Response:
        placeholder = get_placeholder(content_type_id, object_id, slot)
        if placeholder is None:
            raise Http404
        source = placeholder.content_type.model_class().objects.filter(pk=placeholder.object_id).first()
        if source is None:
            raise Http404
        # Check if the user has permission to view the page (should the placeholder be on a page)
        if isinstance(source, PageContent) and not user_can_view_page(request.user, source.page):
            raise Http404
        serializer = PlaceholderSerializer(request, placeholder, language, read_only=True)
        return Response(serializer.data)
