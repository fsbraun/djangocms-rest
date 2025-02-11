from django.urls import path

from djangocms_rest.views import LanguageListView, PageDetailView, PageTreeListView, PlaceholderDetailView

urlpatterns = [
    path("languages/", LanguageListView.as_view(), name="language-list"),
    path("<slug:language>/pages-tree/", PageTreeListView.as_view(), name="page-tree-list"),
    path("<slug:language>/pages-root/", PageDetailView.as_view(), name="page-root"),
    path("<slug:language>/pages/<path:path>/", PageDetailView.as_view(), name="page-detail"),
    path(
        "<slug:language>/placeholders/<int:content_type_id>/<int:object_id>/<str:slot>/",
        PlaceholderDetailView.as_view(),
        name="placeholder-detail",
    ),
]
