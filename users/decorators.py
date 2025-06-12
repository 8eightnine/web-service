from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden


def permission_required(permission, raise_exception=True):
    """
    Декоратор для проверки разрешений пользователя
    
    Args:
        permission (str): Название разрешения в формате 'app_label.permission_codename'
        raise_exception (bool): Если True, вызывает PermissionDenied, иначе редирект
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.has_perm(permission):
                return view_func(request, *args, **kwargs)
            else:
                if raise_exception:
                    raise PermissionDenied("У вас нет прав для выполнения этого действия.")
                else:
                    messages.error(request, "У вас нет прав для выполнения этого действия.")
                    return redirect('photo_list')
        return _wrapped_view
    return decorator


def group_required(group_name, raise_exception=True):
    """
    Декоратор для проверки принадлежности к группе
    
    Args:
        group_name (str): Название группы
        raise_exception (bool): Если True, вызывает PermissionDenied, иначе редирект
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.groups.filter(name=group_name).exists():
                return view_func(request, *args, **kwargs)
            else:
                if raise_exception:
                    raise PermissionDenied(f"Вы должны быть в группе '{group_name}' для выполнения этого действия.")
                else:
                    messages.error(request, f"Вы должны быть в группе '{group_name}' для выполнения этого действия.")
                    return redirect('photo_list')
        return _wrapped_view
    return decorator


def multiple_permissions_required(permissions, require_all=True):
    """
    Декоратор для проверки нескольких разрешений
    
    Args:
        permissions (list): Список разрешений
        require_all (bool): True - нужны все разрешения, False - достаточно одного
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            user_permissions = [request.user.has_perm(perm) for perm in permissions]
            
            if require_all:
                has_permission = all(user_permissions)
                error_msg = f"У вас нет всех необходимых разрешений: {', '.join(permissions)}"
            else:
                has_permission = any(user_permissions)
                error_msg = f"У вас нет ни одного из разрешений: {', '.join(permissions)}"
            
            if has_permission:
                return view_func(request, *args, **kwargs)
            else:
                raise PermissionDenied(error_msg)
        return _wrapped_view
    return decorator


def staff_required(view_func):
    """
    Декоратор для проверки статуса персонала
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_staff:
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied("Доступ только для персонала.")
    return _wrapped_view


def superuser_required(view_func):
    """
    Декоратор для проверки статуса суперпользователя
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied("Доступ только для суперпользователей.")
    return _wrapped_view