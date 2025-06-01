from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_page, name='home'),  # Главная страница
    path('photos/', include('photos.urls')),
    path('login/', views.login_view, name='login'),  # Страница входа
    path('register/', views.register_view, name='register'),  # Страница регистрации
    path('logout/', views.logout_view, name='logout'),  # Заменяем LogoutView на нашу функцию
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
