from django.urls import path, register_converter
from . import views, converters


register_converter(converters.StringConverter, 'string')
register_converter(converters.YearConverter, 'year')

urlpatterns = [
    path('', views.photo_list, name='photo_list'),
    path('<int:pk>/', views.photo_detail, name='photo_detail'),
    path('year/<year:year>/', views.photos_by_year, name='photos_by_year'),
    path('redirect/', views.redirect_to_home, name='redirect_to_home'),
    path('upload/', views.upload_photo, name='upload_photo'),
]