import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'photoboard.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings
import logging

# Включаем подробное логирование
logging.basicConfig(level=logging.DEBUG)

def test_email():
    try:
        print("Настройки email:")
        print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
        print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
        print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
        print(f"EMAIL_USE_SSL: {settings.EMAIL_USE_SSL}")
        print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        print("-" * 50)
        
        result = send_mail(
            subject='Тестовое письмо от Django',
            message='Это тестовое сообщение для проверки SMTP.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['buzmakov.2021@stud.nstu.ru'],  # Замените на ваш email
            fail_silently=False,
        )
        
        print(f"Результат отправки: {result}")
        if result == 1:
            print("✅ Письмо успешно отправлено!")
        else:
            print("❌ Письмо не было отправлено")
            
    except Exception as e:
        print(f"❌ Ошибка при отправке: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_email()