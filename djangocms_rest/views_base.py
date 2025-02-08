from django.utils.functional import cached_property
from rest_framework.views import APIView


class BaseAPIView(APIView):
    # This is a base class for all API views. It sets the allowed methods to GET and OPTIONS.
    http_method_names = ("get", "options")

    @cached_property
    def site(self):
        """
        Lazily fetch and cache the current site, avoiding circular imports.
        """
        from django.contrib.sites.shortcuts import get_current_site  # Lazy import

        return get_current_site(self.request)
