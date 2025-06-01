from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Profile
from .forms import ProfileForm, UserUpdateForm


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
    
    context = {
        'profile_user': user,
        'profile': profile,
        'user_photos': user_photos,
        'is_own_profile': request.user == user,
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
                return redirect('profile_view')
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
