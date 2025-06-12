from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    bio = models.TextField('О себе', max_length=500, blank=True)
    birth_date = models.DateField('Дата рождения', null=True, blank=True)
    avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'
        
        # Добавляем пользовательские разрешения
        permissions = [
            ("can_view_all_profiles", "Может просматривать все профили пользователей"),
            ("can_edit_any_profile", "Может редактировать любой профиль"),
            ("can_manage_user_roles", "Может управлять ролями пользователей"),
        ]

    def __str__(self):
        return f'Профиль пользователя {self.user.username}'

    def get_full_name(self):
        return f'{self.user.first_name} {self.user.last_name}'.strip() or self.user.username

    @classmethod
    def get_or_create_for_user(cls, user):
        """Получить или создать профиль для пользователя"""
        profile, created = cls.objects.get_or_create(user=user)
        return profile