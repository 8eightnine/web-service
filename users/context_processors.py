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
    return {}