from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from . import views

urlpatterns = [
    path("", views.LanguageList.as_view(), name="cms-language-list"),
    path("<slug:language>/pages", views.PageList.as_view(), name="cms-page-list"),
    path("<slug:language>/pages/", views.PageDetail.as_view(), name="cms-page-root"),
    path("<slug:language>/pages/<path:path>/", views.PageDetail.as_view(), name="cms-page-detail"),
    path(
        "<slug:language>/placeholders/<int:content_type_id>/<int:object_id>/<str:slot>/",
        views.PlaceholderDetail.as_view(),
        name="cms-placeholder-detail",
    ),
]

urlpatterns = format_suffix_patterns(urlpatterns)
