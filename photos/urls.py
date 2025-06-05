from django.urls import path, register_converter, re_path
from . import views, converters

register_converter(converters.StringConverter, 'string')
register_converter(converters.YearConverter, 'year')

urlpatterns = [
    # Class-based views
    path('', views.PhotoListView.as_view(), name='photo_list'),
    path('<int:pk>/', views.PhotoDetailView.as_view(), name='photo_detail'),
    path('photo/<slug:slug>/',
         views.PhotoDetailView.as_view(),
         name='photo_detail_slug'),
    path('photo/<slug:slug>/edit/',
         views.EditPhotoView.as_view(),
         name='edit_photo'),
    path('photo/<slug:slug>/delete/',
         views.DeletePhotoView.as_view(),
         name='delete_photo'),
    path('year/<year:year>/',
         views.PhotosByYearView.as_view(),
         name='photos_by_year'),
    path('tag/<slug:tag_slug>/',
         views.PhotosByTagView.as_view(),
         name='photos_by_tag'),
    path('category/<slug:category_slug>/',
         views.PhotosByCategoryView.as_view(),
         name='photos_by_category'),
    path('tags/', views.TagListView.as_view(), name='tag_list'),
    path('stats/', views.StatsView.as_view(), name='stats'),
    path('redirect/',
         views.RedirectToHomeView.as_view(),
         name='redirect_to_home'),
    # Upload views
    path('upload/', views.UploadPhotoView.as_view(), name='upload_photo'),
    path('upload-non-model/',
         views.UploadPhotoNonModelView.as_view(),
         name='upload_photo_non_model'),
    # Support for Cyrillic tags
    re_path(r'^tag/(?P<tag_slug>[\w\-а-яё]+)/$',
            views.PhotosByTagView.as_view(),
            name='photos_by_tag'),
]
