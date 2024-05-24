from cms.models import Page, PageUrl, Placeholder
from cms.utils.conf import get_languages
from cms.utils.i18n import get_language_tuple
from django.contrib.sites.models import Site
from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView as DRFAPIView

from djangocms_rest.serializers.pageserializer import PageSerializer, RESTPage
from djangocms_rest.serializers.placeholder import PlaceholderSerializer
from djangocms_rest.serializers.site import SiteSerializer


class APIView(DRFAPIView):
    http_method_names = ('get', 'options')


class SiteList(APIView):
    """
    List all sites.
    """

    def get(self, request, format=None):
        pages = Site.objects.all()
        serializer = SiteSerializer(pages, many=True, read_only=True)
        return Response(serializer.data)


class LanguageList(APIView):
    def get(self, request, site_id, format=None):
        languages = get_languages().get(site_id, None)
        if languages is None:
            raise Http404
        return Response(languages)


class PageList(APIView):
    """
    List all pages, or create a new page.
    """
    def get(self, request, site_id, language, format=None):
        allowed_languages = [lang[0] for lang in get_language_tuple(site_id)]
        if language not in allowed_languages:
            raise Http404
        pages = (RESTPage(request, page, language=language) for page in Page.objects.all())
        serializer = PageSerializer(pages, many=True, read_only=True)
        return Response(serializer.data)


class PageDetail(APIView):
    """
    Retrieve, update or delete a page instance.
    """
    def get_object(self, site_id, path):
        page_urls = (
            PageUrl
            .objects
            .get_for_site(Site.objects.get(pk=site_id))
            .filter(path=path)
            .select_related('page__node')
        )
        page_urls = list(page_urls)  # force queryset evaluation to save 1 query
        try:
            page = page_urls[0].page
        except IndexError:
            raise Http404
        else:
            page.urls_cache = {url.language: url for url in page_urls}
        return page

    def get(self, request, site_id, language, path="", format=None):
        allowed_languages = [lang[0] for lang in get_language_tuple(site_id)]
        if language not in allowed_languages:
            raise Http404
        page = self.get_object(site_id, path)
        serializer = PageSerializer(RESTPage(request, page, language=language), read_only=True)
        return Response(serializer.data)


class PlaceholderDetail(APIView):
    def get_placeholder(self, content_type_id, object_id, slot):
        try:
            placeholder = Placeholder.objects.get(
                content_type_id=content_type_id,
                object_id=object_id,
                slot=slot
            )
        except Placeholder.DoesNotExist:
            raise Http404
        return placeholder

    def get(self, request, language, content_type_id, object_id, slot, format=None):
        placeholder = self.get_placeholder(content_type_id, object_id, slot)
        if placeholder is None:
            raise Http404
        serializer = PlaceholderSerializer(request, placeholder, language, read_only=True)
        return Response(serializer.data)
