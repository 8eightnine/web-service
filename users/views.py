from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, PasswordResetView
from django.contrib.auth import logout, login
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseRedirect
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
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
            
            # Автоматически входим в систему после регистрации
            login(self.request, user)
            
            messages.success(
                self.request, 
                f'Добро пожаловать, {user.get_full_name() or user.username}! '
                'Ваш аккаунт успешно создан.'
            )
            
            return super().form_valid(form)
            
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
    else:
        user = request.user
    
    profile, created = Profile.objects.get_or_create(user=user)
    
    # Получаем фотографии пользователя
    from photos.models import Photo
    user_photos = Photo.objects.filter(uploaded_by=user).order_by('-uploaded_at')[:6]
    
    # Статистика пользователя
    total_photos = Photo.objects.filter(uploaded_by=user).count()
    
    context = {
        'profile_user': user,
        'profile': profile,
        'user_photos': user_photos,
        'is_own_profile': request.user == user,
        'total_photos': total_photos,
    }
    
    return render(request, 'users/profile.html', context)


@login_required
def edit_profile(request):
    """Редактирование профиля"""
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            try:
                user_form.save()
                profile_form.save()
                messages.success(request, 'Профиль успешно обновлен!')
                return redirect('users:profile_view')
            except Exception as e:
                messages.error(request, f'Ошибка при обновлении профиля: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)
    
    return render(request, 'users/edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })