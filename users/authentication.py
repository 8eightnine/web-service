from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend

class EmailAuthBackend(BaseBackend):
    """
    Бэкенд для аутентификации пользователей по email адресу
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        user_model = get_user_model()
        try:
            # Пытаемся найти пользователя по email
            user = user_model.objects.get(email=username)
            if user.check_password(password):
                return user
            return None
        except user_model.DoesNotExist:
            return None

    def get_user(self, user_id):
        user_model = get_user_model()
        try:
            return user_model.objects.get(pk=user_id)
        except user_model.DoesNotExist:
            return None