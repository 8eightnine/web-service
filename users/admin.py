from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Profile


class ProfileInline(admin.StackedInline):
    """Инлайн для профиля в админке пользователя"""
    model = Profile
    can_delete = False
    verbose_name_plural = 'Профиль'
    fields = ('bio', 'avatar', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')


class CustomUserAdmin(BaseUserAdmin):
    """Расширенная админка для пользователей"""
    inlines = (ProfileInline,)
    
    # Добавляем информацию о разрешениях в список пользователей
    list_display = BaseUserAdmin.list_display + ('get_groups', 'get_user_permissions_count')
    list_filter = BaseUserAdmin.list_filter + ('groups',)
    
    def get_groups(self, obj):
        """Отображение групп пользователя"""
        return ', '.join([group.name for group in obj.groups.all()]) or 'Нет групп'
    get_groups.short_description = 'Группы'
    
    def get_user_permissions_count(self, obj):
        """Количество индивидуальных разрешений"""
        count = obj.user_permissions.count()
        return f"{count} разрешений" if count > 0 else "Нет разрешений"
    get_user_permissions_count.short_description = 'Индивидуальные разрешения'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Админка для профилей"""
    list_display = ('user', 'get_full_name', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'bio', 'avatar')
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_full_name(self, obj):
        """Полное имя пользователя"""
        return obj.get_full_name()
    get_full_name.short_description = 'Полное имя'


class CustomGroupAdmin(admin.ModelAdmin):
    """Расширенная админка для групп"""
    list_display = ('name', 'get_permissions_count', 'get_users_count')
    filter_horizontal = ('permissions',)
    search_fields = ('name',)
    
    def get_permissions_count(self, obj):
        """Количество разрешений в группе"""
        count = obj.permissions.count()
        return f"{count} разрешений"
    get_permissions_count.short_description = 'Разрешения'
    
    def get_users_count(self, obj):
        """Количество пользователей в группе"""
        count = obj.user_set.count()
        return f"{count} пользователей"
    get_users_count.short_description = 'Пользователи'


class CustomPermissionAdmin(admin.ModelAdmin):
    """Админка для разрешений с фильтрацией"""
    list_display = ('name', 'codename', 'content_type', 'is_custom_permission')
    list_filter = ('content_type', 'content_type__app_label')
    search_fields = ('name', 'codename')
    ordering = ('content_type__app_label', 'content_type__model', 'codename')
    
    def is_custom_permission(self, obj):
        """Определяет, является ли разрешение пользовательским"""
        custom_codenames = [
            'can_publish_photos', 'can_feature_photos', 'can_moderate_comments',
            'can_view_all_profiles', 'can_edit_any_profile', 'can_upload_unlimited',
            'can_manage_user_roles'
        ]
        return obj.codename in custom_codenames
    is_custom_permission.boolean = True
    is_custom_permission.short_description = 'Пользовательское'


# Настройка заголовков админ-панели
admin.site.site_header = 'Администрирование Photo Service'
admin.site.site_title = 'Photo Service Admin'
admin.site.index_title = 'Панель управления'