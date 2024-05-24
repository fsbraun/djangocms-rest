from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from . import views

urlpatterns = [
    path('', views.SiteList.as_view()),
    path('<int:site_id>/languages/', views.LanguageList.as_view()),
    path('<int:site_id>/<slug:language>/pages', views.PageList.as_view()),
    path('<int:site_id>/<slug:language>/pages/', views.PageDetail.as_view()),
    path('<int:site_id>/<slug:language>/pages/<path:path>/', views.PageDetail.as_view()),
    path(
        'placeholders/<slug:language>/<int:content_type_id>/<int:object_id>/<str:slot>/',
        views.PlaceholderDetail.as_view(),
        name='placeholder-detail',
    ),
]

urlpatterns = format_suffix_patterns(urlpatterns)
