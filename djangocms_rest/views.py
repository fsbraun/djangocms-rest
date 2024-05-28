from cms.models import Page, PageUrl, Placeholder, PageContent
from cms.utils.conf import get_languages
from cms.utils.i18n import get_language_tuple
from cms.utils.page_permissions import user_can_view_page
from django.contrib.sites.shortcuts import get_current_site
from django.http import Http404
from django.urls import reverse
from rest_framework.response import Response
from rest_framework.views import APIView as DRFAPIView

from djangocms_rest.serializers.pageserializer import PageContentSerializer
from djangocms_rest.serializers.placeholder import PlaceholderSerializer


class APIView(DRFAPIView):
    # This is a base class for all API views. It sets the allowed methods to GET and OPTIONS.
    http_method_names = ("get", "options")


class LanguageList(APIView):
    """
    List of languages available for the site. For each language the API returns the
    link to the list of pages for that languages.
    """

    def get(self, request, format=None):
        languages = get_languages().get(get_current_site(request).id, None)
        if languages is None:
            raise Http404
        for conf in languages:
            conf["pages"] = f"{request.scheme}://{request.get_host()}" + reverse(
                "cms-page-list", args=(conf["code"],)
            )
        return Response(languages)


class PageList(APIView):
    """List of all pages on this site for a given language."""

    def get(self, request, language, format=None):
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
        serializer = PageContentSerializer(request, pages, many=True, read_only=True)
        return Response(serializer.data)


class PageDetail(APIView):
    """
    Retrieve a page instance. The page instance includes the placeholders and
    their links to retrieve dynamic content.
    """

    def get_object(self, site, path):
        page_urls = (
            PageUrl.objects.get_for_site(site)
            .filter(path=path)
            .select_related("page__node")
        )
        page_urls = list(page_urls)  # force queryset evaluation to save 1 query
        try:
            page = page_urls[0].page
        except IndexError:
            raise Http404
        else:
            page.urls_cache = {url.language: url for url in page_urls}
        return page

    def get(self, request, language, path="", format=None):
        site = get_current_site(request)
        allowed_languages = [lang[0] for lang in get_language_tuple(site.pk)]
        if language not in allowed_languages:
            raise Http404
        page = self.get_object(site, path)

        # Check if the user has permission to view the page
        if not user_can_view_page(request.user, page):
            raise Http404

        serializer = PageContentSerializer(
            request, page.get_content_obj(language, fallback=True), read_only=True
        )
        return Response(serializer.data)


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

    def get_placeholder(self, content_type_id, object_id, slot):
        try:
            placeholder = Placeholder.objects.get(
                content_type_id=content_type_id, object_id=object_id, slot=slot
            )
        except Placeholder.DoesNotExist:
            raise Http404
        return placeholder

    def get(self, request, language, content_type_id, object_id, slot, format=None):
        placeholder = self.get_placeholder(content_type_id, object_id, slot)
        if placeholder is None:
            raise Http404
        source = (
            placeholder.content_type.model_class()
            .objects.filter(pk=placeholder.object_id)
            .first()
        )
        if source is None:
            raise Http404
        # Check if the user has permission to view the page (should the placeholder be on a page)
        if isinstance(source, PageContent) and not user_can_view_page(
            request.user, source.page
        ):
            raise Http404
        serializer = PlaceholderSerializer(
            request, placeholder, language, read_only=True
        )
        return Response(serializer.data)
