from django.urls import path, register_converter
from . import views, converters

register_converter(converters.StringConverter, 'string')
register_converter(converters.YearConverter, 'year')

urlpatterns = [
    path('', views.photo_list, name='photo_list'),
    path('<int:pk>/', views.photo_detail, name='photo_detail'),
    path('photo/<slug:slug>/', views.photo_detail, name='photo_detail_slug'),
    path('photo/<slug:slug>/edit/', views.edit_photo, name='edit_photo'),
    path('photo/<slug:slug>/delete/', views.delete_photo, name='delete_photo'),
    path('year/<year:year>/', views.photos_by_year, name='photos_by_year'),
    path('tag/<slug:tag_slug>/', views.photos_by_tag, name='photos_by_tag'),
        path('category/<slug:category_slug>/',
         views.photos_by_category,
         name='photos_by_category'),
    path('tags/', views.tag_list, name='tag_list'),
    path('stats/', views.stats_view, name='stats'),
    path('redirect/', views.redirect_to_home, name='redirect_to_home'),
    path('upload/', views.upload_photo, name='upload_photo'),
]
