from django import template
from django.template.defaultfilters import stringfilter
from datetime import datetime
from django.utils import timezone

register = template.Library()


@register.filter
@stringfilter
def truncate_title(value, length=20):
    """Обрезает заголовок до указанной длины и добавляет '...'"""
    if len(value) > length:
        return value[:length] + '...'
    return value


@register.filter
def time_since_upload(upload_date):
    """Возвращает время, прошедшее с момента загрузки"""
    now = timezone.now()
    if not timezone.is_aware(upload_date):
        upload_date = timezone.make_aware(upload_date)

    diff = now - upload_date
    days = diff.days

    if days == 0:
        hours = diff.seconds // 3600
        if hours == 0:
            minutes = diff.seconds // 60
            return f"{minutes} минут назад"
        return f"{hours} часов назад"
    elif days == 1:
        return "Вчера"
    elif days < 7:
        return f"{days} дней назад"
    else:
        return upload_date.strftime("%d.%m.%Y")


@register.filter
@stringfilter
def add_hashtag(value):
    """Добавляет hashtag перед каждым словом"""
    words = value.split()
    return ' '.join([f'#{word}' for word in words])
