from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.HomePageView.as_view(), name='home'),  # CBV for main page
    path('photos/', include('photos.urls')),
    path('login/', views.LoginView.as_view(), name='login'),  # CBV for login
    path('register/', views.RegisterView.as_view(),
         name='register'),  # CBV for registration
    path('logout/', views.LogoutView.as_view(),
         name='logout'),  # CBV for logout
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
