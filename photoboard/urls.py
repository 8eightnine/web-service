from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_page, name='home'),
    path('login/', views.login_page, name='login_page'),
    path('photos/', include('photos.urls')),
    path('users/', include('users.urls', namespace="users")),  # Добавляем URLs пользователей
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
