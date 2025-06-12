from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, PasswordResetView
from django.contrib.auth import logout, login
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseRedirect
from django.views.generic import CreateView
from django.db import transaction
from django.core.exceptions import PermissionDenied
from .models import Profile
from .forms import ProfileForm, UserUpdateForm, UserRegistrationForm, CustomPasswordResetForm


class LoginUser(LoginView):
    """Представление для входа в систему"""
    template_name = 'users/login.html'
    extra_context = {'title': 'Авторизация'}

    def get_success_url(self):
        return reverse_lazy('photo_list')


class RegisterUser(CreateView):
    """Представление для регистрации пользователя"""
    form_class = UserRegistrationForm
    template_name = 'users/register.html'
    extra_context = {'title': 'Регистрация'}
    success_url = reverse_lazy('photo_list')

    def form_valid(self, form):
        """Обработка успешной регистрации"""
        try:
            # Сохраняем пользователя
            user = form.save()
            
            # Создаем профиль вручную
            Profile.objects.get_or_create(user=user)
            
            # Входим в систему
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(self.request, user)
            
            messages.success(self.request, 'Регистрация прошла успешно!')
            return redirect(self.success_url)
            
        except Exception as e:
            messages.error(self.request, f'Ошибка при регистрации: {str(e)}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Обработка ошибок в форме"""
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        """Добавление дополнительного контекста"""
        context = super().get_context_data(**kwargs)
        context['show_login_link'] = True
        return context


class CustomPasswordResetView(PasswordResetView):
    """Кастомное представление для сброса пароля с проверкой email"""
    form_class = CustomPasswordResetForm
    template_name = 'users/password_reset_form.html'
    email_template_name = 'users/password_reset_email.html'
    success_url = reverse_lazy('users:password_reset_done')
    extra_context = {'title': 'Восстановление пароля'}

    def form_valid(self, form):
        """Обработка успешной отправки формы"""
        messages.success(
            self.request,
            'Инструкции по восстановлению пароля отправлены на указанный email адрес.'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        """Обработка ошибок в форме"""
        messages.error(
            self.request,
            'Пожалуйста, исправьте ошибки в форме.'
        )
        return super().form_invalid(form)


def logout_user(request):
    """Выход из системы"""
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы.')
    return HttpResponseRedirect(reverse('users:login'))


@login_required
def profile_view(request, username=None):
    """Просмотр профиля пользователя"""
    if username:
        user = get_object_or_404(User, username=username)
        # Проверяем разрешение на просмотр чужих профилей
        if user != request.user and not request.user.has_perm('users.can_view_all_profiles'):
            messages.error(request, 'У вас нет прав для просмотра этого профиля.')
            return redirect('users:profile_view')
    else:
        user = request.user
    
    profile, created = Profile.objects.get_or_create(user=user)
    
    # Получаем фотографии пользователя
    try:
        from photos.models import Photo
        user_photos = Photo.objects.filter(uploaded_by=user).order_by('-uploaded_at')[:6]
        total_photos = Photo.objects.filter(uploaded_by=user).count()
    except ImportError:
        user_photos = []
        total_photos = 0
    
    context = {
        'profile_user': user,
        'profile': profile,
        'user_photos': user_photos,
        'is_own_profile': request.user == user,
        'total_photos': total_photos,
        'user_permissions': {
            'can_edit_any_profile': request.user.has_perm('users.can_edit_any_profile'),
            'can_view_all_profiles': request.user.has_perm('users.can_view_all_profiles'),
            'can_moderate_comments': request.user.has_perm('users.can_moderate_comments'),
            'can_manage_user_roles': request.user.has_perm('users.can_manage_user_roles'),
        },
        'user_groups': {
            'is_moderator': request.user.groups.filter(name='Модераторы').exists(),
            'is_admin': request.user.groups.filter(name='Администраторы контента').exists(),
        }
    }
    
    return render(request, 'users/profile.html', context)


@login_required
def edit_profile(request, username=None):
    """Редактирование профиля"""
    if username:
        user = get_object_or_404(User, username=username)
        # Проверяем права на редактирование чужого профиля
        if user != request.user and not request.user.has_perm('users.can_edit_any_profile'):
            messages.error(request, 'У вас нет прав для редактирования этого профиля.')
            return redirect('users:profile_view')
    else:
        user = request.user
    
    profile, created = Profile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            try:
                with transaction.atomic():
                    user_form.save()
                    profile_form.save()
                    messages.success(request, 'Профиль успешно обновлен!')
                    if username:
                        return redirect('users:profile_view_user', username=user.username)
                    else:
                        return redirect('users:profile_view')
            except Exception as e:
                messages.error(request, f'Ошибка при обновлении профиля: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile_user': user,
        'is_own_profile': request.user == user,
    }
    
    return render(request, 'users/edit_profile.html', context)


@login_required
def all_profiles_view(request):
    """Просмотр всех профилей (только для пользователей с соответствующим разрешением)"""
    if not request.user.has_perm('users.can_view_all_profiles'):
        messages.error(request, "У вас нет прав для просмотра всех профилей.")
        return redirect('photo_list')
    
    profiles = Profile.objects.select_related('user').all().order_by('-created_at')
    
    context = {
        'profiles': profiles,
        'title': 'Все профили пользователей'
    }
    
    return render(request, 'users/all_profiles.html', context)


@login_required
def moderator_panel(request):
    """Панель модератора"""
    if not request.user.groups.filter(name='Модераторы').exists() and not request.user.is_staff:
        messages.error(request, "Доступ только для модераторов.")
        return redirect('photo_list')
    
    from django.contrib.auth.models import Group
    
    # Статистика
    total_users = User.objects.count()
    total_profiles = Profile.objects.count()
    try:
        moderators_count = Group.objects.get(name='Модераторы').user_set.count()
    except Group.DoesNotExist:
        moderators_count = 0
    
    # Последние зарегистрированные пользователи
    recent_users = User.objects.select_related('profile').order_by('-date_joined')[:10]
    
    context = {
        'total_users': total_users,
        'total_profiles': total_profiles,
        'moderators_count': moderators_count,
        'recent_users': recent_users,
        'title': 'Панель модератора'
    }
    
    return render(request, 'users/moderator_panel.html', context)


@login_required
def manage_user_roles(request, user_id):
    """Управление ролями пользователя"""
    if not request.user.has_perm('users.can_manage_user_roles'):
        raise PermissionDenied("У вас нет прав для управления ролями пользователей.")
    
    from django.contrib.auth.models import Group, Permission
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Обработка изменения групп
                selected_groups = request.POST.getlist('groups')
                user.groups.clear()
                for group_id in selected_groups:
                    try:
                        group = Group.objects.get(id=group_id)
                        user.groups.add(group)
                    except Group.DoesNotExist:
                        continue
                
                # Обработка индивидуальных разрешений
                selected_permissions = request.POST.getlist('permissions')
                user.user_permissions.clear()
                for perm_id in selected_permissions:
                    try:
                        permission = Permission.objects.get(id=perm_id)
                        user.user_permissions.add(permission)
                    except Permission.DoesNotExist:
                        continue
                
                messages.success(request, f'Роли пользователя {user.username} успешно обновлены!')
                return redirect('users:manage_user_roles', user_id=user.id)
                
        except Exception as e:
            messages.error(request, f'Ошибка при обновлении ролей: {str(e)}')
    
    # Получаем все группы и разрешения
    all_groups = Group.objects.all()
    all_permissions = Permission.objects.filter(
        content_type__app_label__in=['users', 'photos']
    ).select_related('content_type')
    
    context = {
        'profile_user': user,
        'all_groups': all_groups,
        'all_permissions': all_permissions,
        'user_groups': user.groups.all(),
        'user_permissions': user.user_permissions.all(),
        'title': f'Управление ролями - {user.username}'
    }
    
    return render(request, 'users/manage_user_roles.html', context)

