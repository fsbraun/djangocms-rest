from django.urls import path

from . import views

urlpatterns = [
    path("languages/", views.LanguageListView.as_view(), name="cms-language-list"),
    path("<slug:language>/pages-tree/", views.PageTreeListView.as_view(), name="cms-page-tree-list"),
    path("<slug:language>/pages-root/", views.PageDetailView.as_view(), name="cms-page-root"),
    path("<slug:language>/pages/<path:path>/", views.PageDetailView.as_view(), name="cms-page-detail"),
    path(
        "<slug:language>/placeholders/<int:content_type_id>/<int:object_id>/<str:slot>/",
        views.PlaceholderDetailView.as_view(),
        name="cms-placeholder-detail",
    ),
]
