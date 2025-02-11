import time
from datetime import datetime

from cms.cache.placeholder import (
    _get_placeholder_cache_key,
    _get_placeholder_cache_version_key,
)
from cms.utils.conf import get_cms_setting


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
        _set_placeholder_cache_version(placeholder, lang, site_id, version, vary_on_list)
    return version, vary_on_list


def _set_placeholder_cache_version(placeholder, lang, site_id, version, vary_on_list=None, duration=None):
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
        placeholder.get_cache_expiration(request, datetime.now()),
    )
    cache.set(key, content, duration)
    # "touch" the cache-version, so that it stays as fresh as this content.
    version, vary_on_list = _get_placeholder_cache_version(placeholder, lang, site_id)
    _set_placeholder_cache_version(placeholder, lang, site_id, version, vary_on_list, duration=duration)


def get_placeholder_rest_cache(placeholder, lang, site_id, request):
    """
    Returns the placeholder from cache respecting the placeholder's
    VARY headers.
    """
    from django.core.cache import cache

    key = _get_placeholder_cache_key(placeholder, lang, site_id, request, soft=True) + ":rest"
    content = cache.get(key)
    return content
