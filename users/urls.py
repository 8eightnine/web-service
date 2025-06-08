from django.urls import path
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from . import views

app_name = "users"

urlpatterns = [
    # Аутентификация
    path('login/', views.LoginUser.as_view(), name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.RegisterUser.as_view(), name='register'),
    
    # Профили
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/<str:username>/', views.profile_view, name='profile_view_user'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    
    # Смена пароля
    path('password-change/',
         auth_views.PasswordChangeView.as_view(
             template_name="users/password_change_form.html",
             success_url=reverse_lazy("users:password_change_done")
         ),
         name='password_change'),
    path('password-change/done/',
         auth_views.PasswordChangeDoneView.as_view(
             template_name="users/password_change_done.html"
         ),
         name='password_change_done'),
    
    # Восстановление пароля с кастомной проверкой
    path('password-reset/',
         views.CustomPasswordResetView.as_view(),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name="users/password_reset_done.html"
         ),
         name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name="users/password_reset_confirm.html",
             success_url=reverse_lazy("users:password_reset_complete")
         ),
         name='password_reset_confirm'),
    path('password-reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name="users/password_reset_complete.html"
         ),
         name='password_reset_complete'),
]
