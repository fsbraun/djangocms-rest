from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path


admin.autodiscover()

urlpatterns = [
    path("api/", include("djangocms_rest.urls")),
]

urlpatterns += staticfiles_urlpatterns()
