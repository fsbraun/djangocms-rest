from django.urls import path

from djangocms_rest.views import LanguageListView, PageDetailView, PageTreeListView, PlaceholderDetailView

urlpatterns = [
    path("languages/", LanguageListView.as_view(), name="cms-language-list"),
    path("<slug:language>/pages-tree/", PageTreeListView.as_view(), name="cms-page-tree-list"),
    path("<slug:language>/pages-root/", PageDetailView.as_view(), name="cms-page-root"),
    path("<slug:language>/pages/<path:path>/", PageDetailView.as_view(), name="cms-page-detail"),
    path(
        "<slug:language>/placeholders/<int:content_type_id>/<int:object_id>/<str:slot>/",
        PlaceholderDetailView.as_view(),
        name="cms-placeholder-detail",
    ),
]
