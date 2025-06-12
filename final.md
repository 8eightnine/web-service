# Отчет о реализации системы групп и разрешений

## 1. Обзор проделанной работы

В рамках проекта была реализована полноценная система управления группами пользователей и разрешениями, которая включает:

- Создание пользовательских разрешений
- Настройка групп пользователей с различными ролями
- Контроль доступа к функциям системы
- Административные инструменты для управления ролями
- Интеграция с шаблонами для условного отображения контента

## 2. Созданные пользовательские разрешения

### 2.1 Список разрешений

Были созданы следующие пользовательские разрешения:

```python
custom_permissions = [
    {
        'codename': 'can_publish_photos',
        'name': 'Может публиковать фотографии без модерации',
        'content_type': photo_content_type
    },
    {
        'codename': 'can_feature_photos',
        'name': 'Может отмечать фотографии как рекомендуемые',
        'content_type': photo_content_type
    },
    {
        'codename': 'can_moderate_comments',
        'name': 'Может модерировать комментарии',
        'content_type': photo_content_type
    },
    {
        'codename': 'can_view_all_profiles',
        'name': 'Может просматривать все профили пользователей',
        'content_type': profile_content_type
    },
    {
        'codename': 'can_edit_any_profile',
        'name': 'Может редактировать любой профиль',
        'content_type': profile_content_type
    },
    {
        'codename': 'can_upload_unlimited',
        'name': 'Может загружать неограниченное количество фото',
        'content_type': photo_content_type
    }
]
```

### 2.2 Команда для создания разрешений

Создана Django management команда для автоматической настройки системы разрешений:

```python:users/management/commands/setup_permissions.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from users.models import Profile
from photos.models import Photo

class Command(BaseCommand):
    help = 'Настройка групп разрешений и пользователей'

    def handle(self, *args, **options):
        self.stdout.write('Начинаем настройку разрешений...')
        
        # Создаем группы
        self.create_groups()
        
        # Создаем пользовательские разрешения
        self.create_custom_permissions()
        
        # Создаем тестовых пользователей
        self.create_test_users()
        
        # Назначаем разрешения
        self.assign_permissions()
        
        self.stdout.write(
            self.style.SUCCESS('Настройка разрешений завершена успешно!')
        )
```

## 3. Система групп пользователей

### 3.1 Созданные группы

Реализованы следующие группы пользователей:

1. **Модераторы** - управление контентом и пользователями
2. **Редакторы** - создание и редактирование контента
3. **VIP Пользователи** - расширенные возможности загрузки

### 3.2 Распределение разрешений по группам

```python
# Разрешения для модераторов
moderator_permissions = [
    'can_moderate_comments',
    'can_feature_photos',
    'can_view_all_profiles',
    'delete_photo',
    'change_photo',
]

# Разрешения для редакторов
editor_permissions = [
    'can_publish_photos',
    'can_feature_photos',
    'add_photo',
    'change_photo',
]

# Разрешения для VIP пользователей
vip_permissions = [
    'can_upload_unlimited',
    'can_publish_photos',
]
```

## 4. Контроль доступа в представлениях

### 4.1 Защита представлений с помощью разрешений

```python:users/views.py
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
    
    # Логика панели модератора
    ...
```

### 4.2 Контроль доступа к редактированию фотографий

```python:photos/views.py
def get_object(self, queryset=None):
    """Get photo object with user permission checks"""
    obj = super().get_object(queryset)
    if obj.uploaded_by != self.request.user and not self.request.user.is_staff:
        messages.error(self.request,
                       'У вас нет прав для редактирования этой фотографии.')
        raise Http404("Нет прав для редактирования")
    return obj
```

## 5. Контекстный процессор для разрешений

### 5.1 Создание контекстного процессора

Для удобного использования разрешений в шаблонах создан контекстный процессор:

```python:users/context_processors.py
def user_permissions(request):
    """
    Контекстный процессор для добавления разрешений пользователя в контекст шаблонов
    """
    if request.user.is_authenticated:
        return {
            'user_permissions': {
                'can_view_all_profiles': request.user.has_perm('users.can_view_all_profiles'),
                'can_edit_any_profile': request.user.has_perm('users.can_edit_any_profile'),
                'can_moderate_comments': request.user.has_perm('users.can_moderate_comments'),
                'can_manage_user_roles': request.user.has_perm('users.can_manage_user_roles'),
                'can_publish_photos': request.user.has_perm('users.can_publish_photos'),
                'can_feature_photos': request.user.has_perm('users.can_feature_photos'),
                'can_upload_unlimited': request.user.has_perm('users.can_upload_unlimited'),
            },
            'user_groups': {
                'is_moderator': request.user.groups.filter(name='Модераторы').exists(),
                'is_admin': request.user.groups.filter(name='Администраторы контента').exists(),
                'is_user': request.user.groups.filter(name='Пользователи').exists(),
            }
        }
    return {
        'user_permissions': {},
        'user_groups': {}
    }
```

### 5.2 Регистрация в настройках

```python:settings.py
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'users.context_processors.user_permissions',  # Добавлен контекстный процессор
            ],
        },
    },
]
```

## 6. Условное отображение в шаблонах

### 6.1 Использование разрешений в навигации

```html:photos/templates/base.html
{% if user.is_authenticated %}
    <li class="nav-item dropdown">
        <a class="nav-link dropdown-toggle" href="#" id="userDropdown" role="button" 
           data-bs-toggle="dropdown" aria-expanded="false">
            <i class="fas fa-user"></i> {{ user.get_full_name|default:user.username }}
        </a>
        <ul class="dropdown-menu" aria-labelledby="userDropdown">
            <li><a class="dropdown-item" href="{% url 'users:profile_view' %}">
                <i class="fas fa-user"></i> Мой профиль
            </a></li>
            
            {% if perms.users.can_view_all_profiles %}
                <li><hr class="dropdown-divider"></li>
                <li><a class="dropdown-item" href="{% url 'users:all_profiles' %}">
                    <i class="fas fa-users"></i> Все профили
                </a></li>
            {% endif %}
            
            {% if user_groups.is_moderator %}
                <li><a class="dropdown-item" href="{% url 'users:moderator_panel' %}">
                    <i class="fas fa-shield-alt"></i> Панель модератора
                </a></li>
            {% endif %}
        </ul>
    </li>
{% endif %}
```

### 6.2 Панель модератора с проверкой разрешений

```html:users/templates/users/moderator_panel.html
<div class="card-body">
    <ul class="list-unstyled">
        {% if perms.users.can_moderate_comments %}
            <li><i class="fas fa-check text-success"></i> Модерация комментариев</li>
        {% endif %}
        {% if perms.users.can_feature_photos %}
            <li><i class="fas fa-check text-success"></i> Рекомендуемые фотографии</li>
        {% endif %}
        {% if perms.users.can_view_all_profiles %}
            <li><i class="fas fa-check text-success"></i> Просмотр всех профилей</li>
        {% endif %}
        {% if perms.users.can_edit_any_profile %}
            <li><i class="fas fa-check text-success"></i> Редактирование профилей</li>
        {% endif %}
    </ul>
</div>
```

## 7. Административные инструменты

### 7.1 Просмотр всех профилей

Создан интерфейс для просмотра всех профилей пользователей с проверкой разрешений:

```html:users/templates/users/all_profiles.html
<div class="d-grid gap-2">
    <a href="{% url 'users:profile_view_user' profile.user.username %}" 
       class="btn btn-outline-primary btn-sm">
        <i class="fas fa-eye"></i> Просмотр профиля
    </a>
    
    {% if perms.users.can_edit_any_profile %}
        <a href="{% url 'users:edit_profile_user' profile.user.username %}" 
           class="btn btn-outline-secondary btn-sm">
            <i class="fas fa-edit"></i> Редактировать
        </a>
    {% endif %}
    
    {% if perms.users.can_manage_user_roles %}
        <a href="{% url 'users:manage_user_roles' profile.user.id %}" 
           class="btn btn-outline-warning btn-sm">
            <i class="fas fa-user-cog"></i> Роли
        </a>
    {% endif %}
</div>
```

### 7.2 Управление ролями пользователей

Создан интерфейс для управления группами и разрешениями пользователей:

```html:users/templates/users/manage_user_roles.html
<div class="card mb-4">
    <div class="card-header">
        <h5><i class="fas fa-users"></i> Группы пользователей</h5>
    </div>
    <div class="card-body">
        <div class="row">
            {% for group in all_groups %}
                <div class="col-md-6 mb-3">
                    <div class="form-check">
                        <input class="form-check-input" 
                               type="checkbox" 
                               name="groups" 
                               value="{{ group.id }}" 
                               id="group_{{ group.id }}"
                               {% if group in user_groups %}checked{% endif %}>
                        <label class="form-check-label" for="group_{{ group.id }}">
                            <strong>{{ group.name }}</strong>
                            <br>
                            <small class="text-muted">{{ group.permissions.count }} разрешений</small>
                        </label>
                    </div>
                </div>
            {% endfor %}
        </div>
    </div>
</div>
```

## 8. Тестовые пользователи

### 8.1 Создание тестовых аккаунтов

Команда автоматически создает тестовых пользователей для демонстрации системы:

```python
test_users = [
    {
        'username': 'moderator1',
        'email': 'moderator1@example.com',
        'first_name': 'Модератор',
        'last_name': 'Первый',
        'password': 'testpass123'
    },
    {
        'username': 'editor1',
        'email': 'editor1@example.com',
        'first_name': 'Редактор',
        'last_name': 'Первый',
        'password': 'testpass123'
    },
    {
        'username': 'vip_user1',
        'email': 'vip1@example.com',
        'first_name': 'VIP',
        'last_name': 'Пользователь',
        'password': 'testpass123'
    }
]
```

### 8.2 Назначение ролей

````python
# Назначаем пользователей в группы
moderator1 = User.objects.get(username='moderator1')
moderator1.groups.add(moderators)

editor1 = User.objects.get(username='editor1')
editor1.groups.add(editors)

vip_user1 = User.objects.get(username='vip_user1')
vip_user1.groups.add(vip_users)

# Назначаем индивидуальные разрешения
power_user1 = User.objects.get(username='power_user1')
individual_permissions = [
    'can_edit_any_profile',
    'can_view_all_profiles',
    'add_photo',
    'change_photo',
]

for perm_codename in individual_permissions:
    permission = Permission.objects.get(codename=perm_codename)
    power_user1.user_permissions.add(permission)
```

## 9. URL-маршруты для системы разрешений

### 9.1 Полная структура URL

```python:users/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    # Аутентификация
    path('login/', views.LoginUser.as_view(), name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.RegisterUser.as_view(), name='register'),
    
    # Профиль пользователя
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/<str:username>/', views.profile_view, name='profile_view_user'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/edit/<str:username>/', views.edit_profile, name='edit_profile_user'),
    
    # Административные функции
    path('all-profiles/', views.all_profiles_view, name='all_profiles'),
    path('moderator-panel/', views.moderator_panel, name='moderator_panel'),
    path('manage-roles/<int:user_id>/', views.manage_user_roles, name='manage_user_roles'),
    
    # Смена и восстановление пароля
    path('password-change/', 
         auth_views.PasswordChangeView.as_view(
             template_name='users/password_change_form.html',
             success_url='/users/password-change/done/'
         ), 
         name='password_change'),
    path('password-change/done/', 
         auth_views.PasswordChangeDoneView.as_view(
             template_name='users/password_change_done.html'
         ), 
         name='password_change_done'),
    
    path('password-reset/', 
         views.CustomPasswordResetView.as_view(), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='users/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='users/password_reset_confirm.html',
             success_url='/users/password-reset/complete/'
         ), 
         name='password_reset_confirm'),
    path('password-reset/complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='users/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
]
```

## 10. Интеграция с системой фотографий

### 10.1 Контроль доступа к редактированию фотографий

```python:photos/views.py
class PhotoUpdateView(LoginRequiredMixin, UpdateView):
    model = Photo
    form_class = PhotoForm
    template_name = 'photos/edit_photo.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_object(self, queryset=None):
        """Проверка прав доступа к редактированию"""
        obj = super().get_object(queryset)
        if obj.uploaded_by != self.request.user and not self.request.user.is_staff:
            messages.error(self.request,
                           'У вас нет прав для редактирования этой фотографии.')
            raise Http404("Нет прав для редактирования")
        return obj

class PhotoDeleteView(LoginRequiredMixin, DeleteView):
    model = Photo
    template_name = 'photos/delete_photo.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('photo_list')

    def get_object(self, queryset=None):
        """Проверка прав доступа к удалению"""
        obj = super().get_object(queryset)
        if obj.uploaded_by != self.request.user and not self.request.user.is_staff:
            messages.error(self.request,
                           'У вас нет прав для удаления этой фотографии.')
            raise Http404("Нет прав для удаления")
        return obj
```

### 10.2 Условное отображение кнопок управления

```html:photos/templates/photos/photo_detail.html
{% if user.is_authenticated and photo.uploaded_by == user or user.is_staff %}
    <div class="photo-actions mt-3">
        <a href="{% url 'edit_photo' photo.slug %}" class="btn btn-primary">
            <i class="fas fa-edit"></i> Редактировать
        </a>
        <a href="{% url 'delete_photo' photo.slug %}" class="btn btn-danger">
            <i class="fas fa-trash"></i> Удалить
        </a>
    </div>
{% endif %}

{% if perms.users.can_feature_photos %}
    <div class="moderator-actions mt-2">
        <button class="btn btn-warning btn-sm" onclick="toggleFeatured({{ photo.id }})">
            <i class="fas fa-star"></i> 
            {% if photo.is_featured %}Убрать из рекомендуемых{% else %}Добавить в рекомендуемые{% endif %}
        </button>
    </div>
{% endif %}
```

## 11. Статистика и мониторинг

### 11.1 Панель модератора со статистикой

```python:users/views.py
@login_required
def moderator_panel(request):
    """Панель модератора с расширенной статистикой"""
    if not request.user.groups.filter(name='Модераторы').exists() and not request.user.is_staff:
        messages.error(request, "Доступ только для модераторов.")
        return redirect('photo_list')
    
    from django.contrib.auth.models import Group
    from photos.models import Photo
    
    # Статистика пользователей
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()
    
    # Статистика групп
    try:
        moderators_count = Group.objects.get(name='Модераторы').user_set.count()
        editors_count = Group.objects.get(name='Редакторы').user_set.count()
        vip_count = Group.objects.get(name='VIP Пользователи').user_set.count()
    except Group.DoesNotExist:
        moderators_count = editors_count = vip_count = 0
    
    # Статистика контента
    total_photos = Photo.objects.count()
    pending_photos = Photo.objects.filter(is_approved=False).count()
    featured_photos = Photo.objects.filter(is_featured=True).count()
    
    # Последние пользователи
    recent_users = User.objects.select_related('profile').order_by('-date_joined')[:10]
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'staff_users': staff_users,
        'moderators_count': moderators_count,
        'editors_count': editors_count,
        'vip_count': vip_count,
        'total_photos': total_photos,
        'pending_photos': pending_photos,
        'featured_photos': featured_photos,
        'recent_users': recent_users,
        'title': 'Панель модератора'
    }
    
    return render(request, 'users/moderator_panel.html', context)
```

### 11.2 Отображение статистики в шаблоне

```html:users/templates/users/moderator_panel.html
<!-- Статистика пользователей -->
<div class="row mb-4">
    <div class="col-md-3">
        <div class="card text-center bg-primary text-white">
            <div class="card-body">
                <h3>{{ total_users }}</h3>
                <p class="card-text">Всего пользователей</p>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card text-center bg-success text-white">
            <div class="card-body">
                <h3>{{ active_users }}</h3>
                <p class="card-text">Активных</p>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card text-center bg-warning text-white">
            <div class="card-body">
                <h3>{{ moderators_count }}</h3>
                <p class="card-text">Модераторов</p>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card text-center bg-info text-white">
            <div class="card-body">
                <h3>{{ staff_users }}</h3>
                <p class="card-text">Персонала</p>
            </div>
        </div>
    </div>
</div>

<!-- Статистика контента -->
<div class="row mb-4">
    <div class="col-md-4">
        <div class="card text-center">
            <div class="card-body">
                <h3 class="text-primary">{{ total_photos }}</h3>
                <p class="card-text">Всего фотографий</p>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card text-center">
            <div class="card-body">
                <h3 class="text-warning">{{ pending_photos }}</h3>
                <p class="card-text">На модерации</p>
            </div>
        </div>
    </div>
    <div class="col-md-4">
        <div class="card text-center">
            <div class="card-body">
                <h3 class="text-success">{{ featured_photos }}</h3>
                <p class="card-text">Рекомендуемых</p>
            </div>
        </div>
    </div>
</div>
```

## 12. Безопасность и валидация

### 12.1 Проверка разрешений на уровне представлений

```python:users/views.py
def manage_user_roles(request, user_id):
    """Управление ролями пользователя"""
    # Проверка разрешений
    if not request.user.has_perm('users.can_manage_user_roles') and not request.user.is_staff:
        messages.error(request, "У вас нет прав для управления ролями пользователей.")
        return redirect('photo_list')
    
    # Проверка существования пользователя
    profile_user = get_object_or_404(User, id=user_id)
    
    # Запрет изменения собственных разрешений (кроме суперпользователя)
    if profile_user == request.user and not request.user.is_superuser:
        messages.error(request, "Вы не можете изменять собственные разрешения.")
        return redirect('users:moderator_panel')
    
    # Запрет изменения разрешений суперпользователя
    if profile_user.is_superuser and not request.user.is_superuser:
        messages.error(request, "Вы не можете изменять разрешения суперпользователя.")
        return redirect('users:moderator_panel')
```

### 12.2 Валидация в формах

```python:users/forms.py
class UserRoleManagementForm(forms.Form):
    """Форма для управления ролями пользователя"""
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Группы пользователей'
    )
    
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.filter(
            content_type__app_label__in=['users', 'photos']
        ),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Индивидуальные разрешения'
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        # Ограничиваем доступные группы в зависимости от прав текущего пользователя
        if not self.current_user.is_superuser:
            # Обычные модераторы не могут назначать группу "Модераторы"
            self.fields['groups'].queryset = Group.objects.exclude(
                name__in=['Модераторы', 'Администраторы']
            )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Проверяем, что пользователь не пытается назначить себе дополнительные права
        if self.user == self.current_user and not self.current_user.is_superuser:
            raise forms.ValidationError(
                "Вы не можете изменять собственные разрешения."
            )
        
        return cleaned_data
```

## 13. Команды управления

### 13.1 Запуск настройки разрешений

Для инициализации системы разрешений используется команда:

```bash
python manage.py setup_permissions
```

Вывод команды:
```
Начинаем настройку разрешений...
Создаем группы...
  ✓ Создана группа: Модераторы
  ✓ Создана группа: Редакторы
  ✓ Создана группа: VIP Пользователи
Создаем пользовательские разрешения...
  ✓ Создано разрешение: Может публиковать фотографии без модерации
  ✓ Создано разрешение: Может отмечать фотографии как рекомендуемые


