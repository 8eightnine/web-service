from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True, verbose_name="О себе")
    avatar = models.ImageField(
        upload_to='avatars/', 
        blank=True, 
        verbose_name="Аватар",
        help_text="Рекомендуемый размер: 300x300 пикселей"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"
        
        # Добавляем пользовательские разрешения
        permissions = [
            ("can_view_all_profiles", "Может просматривать все профили пользователей"),
            ("can_edit_any_profile", "Может редактировать любой профиль"),
            ("can_manage_user_roles", "Может управлять ролями пользователей"),
        ]

    def __str__(self):
        return f"Профиль {self.user.username}"

    def get_full_name(self):
        """Возвращает полное имя пользователя или username"""
        full_name = self.user.get_full_name()
        return full_name if full_name else self.user.username


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Автоматически создает или обновляет профиль при создании/сохранении пользователя"""
    if created:
        # Создаем профиль только если он не существует
        Profile.objects.get_or_create(user=instance)
    else:
        # Обновляем существующий профиль или создаем новый
        if hasattr(instance, 'profile'):
            instance.profile.save()
        else:
            Profile.objects.get_or_create(user=instance)