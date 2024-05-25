from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path, re_path
from django.views.i18n import JavaScriptCatalog
from django.views.static import serve


admin.autodiscover()

urlpatterns = [
    path("api/", include("djangocms_rest.urls")),
]

urlpatterns += staticfiles_urlpatterns()
