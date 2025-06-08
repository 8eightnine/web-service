from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
import smtplib
import ssl

class Command(BaseCommand):
    help = 'Тестирование отправки email'

    def add_arguments(self, parser):
        parser.add_argument('--to', type=str, help='Email получателя')

    def handle(self, *args, **options):
        recipient = options.get('to') or 'buzmakov.2021@stud.nstu.ru'
        
        self.stdout.write("🔍 Проверка настроек SMTP...")
        self.stdout.write(f"HOST: {settings.EMAIL_HOST}")
        self.stdout.write(f"PORT: {settings.EMAIL_PORT}")
        self.stdout.write(f"USER: {settings.EMAIL_HOST_USER}")
        self.stdout.write(f"USE_SSL: {getattr(settings, 'EMAIL_USE_SSL', True)}")
        self.stdout.write(f"USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', False)}")
        
        # Тест 1: Проверка подключения к SMTP серверу
        self.stdout.write("\n🔌 Тестирование подключения к SMTP...")
        try:
            if settings.EMAIL_USE_SSL:
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT, context=context)
            else:
                server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
                if settings.EMAIL_USE_TLS:
                    server.starttls()
            
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            self.stdout.write(self.style.SUCCESS("✅ Подключение к SMTP успешно!"))
            server.quit()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка подключения к SMTP: {e}"))
            return
        
        # Тест 2: Отправка через Django
        self.stdout.write("\n📧 Отправка тестового письма через Django...")
        try:
            result = send_mail(
                subject='Тестовое письмо Django',
                message='Это тестовое сообщение отправлено из Django приложения.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            
            if result == 1:
                self.stdout.write(self.style.SUCCESS(f"✅ Письмо отправлено на {recipient}"))
            else:
                self.stdout.write(self.style.ERROR("❌ Письмо не было отправлено"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка отправки: {e}"))
            import traceback
            self.stdout.write(traceback.format_exc())