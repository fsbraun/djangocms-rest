from cms.models import Page, PageUrl, Placeholder
from django.contrib.sites.models import Site
from django.http import Http404


def get_object(site: Site, path: str) -> Page:
    page_urls = (
        PageUrl.objects.get_for_site(site)
        .filter(path=path)
        .select_related("page__node")
    )
    page_urls = list(page_urls)
    try:
        page = page_urls[0].page
    except IndexError:
        raise Http404
    else:
        page.urls_cache = {url.language: url for url in page_urls}
    return page

def get_placeholder(content_type_id: int, object_id: int, slot:str) -> Placeholder:
    try:
        placeholder = Placeholder.objects.get(
            content_type_id=content_type_id, object_id=object_id, slot=slot
        )
    except Placeholder.DoesNotExist:
        raise Http404
    return placeholder

