from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def truncate_title(value, length=20):
    """Обрезает заголовок до указанной длины и добавляет '...'"""
    if len(value) > length:
        return value[:length] + '...'
    return value

@register.filter
def user_photos_count(user):
    """Возвращает количество фотографий пользователя"""
    return user.photo_set.count()

@register.simple_tag
def get_recent_photos(user, count=5):
    """Возвращает последние фотографии пользователя"""
    return user.photo_set.all().order_by('-uploaded_at')[:count] 