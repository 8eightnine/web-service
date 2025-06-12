from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Показать информацию о разрешениях и группах'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Показать разрешения конкретного пользователя',
        )
        parser.add_argument(
            '--group',
            type=str,
            help='Показать разрешения конкретной группы',
        )
        parser.add_argument(
            '--custom-only',
            action='store_true',
            help='Показать только пользовательские разрешения',
        )

    def handle(self, *args, **options):
        if options['user']:
            self.show_user_permissions(options['user'])
        elif options['group']:
            self.show_group_permissions(options['group'])
        else:
            self.show_all_permissions(options['custom_only'])

    def show_user_permissions(self, username):
        """Показать разрешения пользователя"""
        try:
            user = User.objects.get(username=username)
            self.stdout.write(
                self.style.SUCCESS(f'\n=== Разрешения пользователя: {user.username} ===')
            )
            
            # Основная информация
            self.stdout.write(f'Полное имя: {user.get_full_name() or "Не указано"}')
            self.stdout.write(f'Email: {user.email}')
            self.stdout.write(f'Суперпользователь: {"Да" if user.is_superuser else "Нет"}')
            self.stdout.write(f'Персонал: {"Да" if user.is_staff else "Нет"}')
            
            # Группы
            groups = user.groups.all()
            if groups:
                self.stdout.write(f'\nГруппы ({groups.count()}):')
                for group in groups:
                    self.stdout.write(f'  • {group.name}')
                    for perm in group.permissions.all():
                        self.stdout.write(f'    - {perm.name} ({perm.codename})')
            else:
                self.stdout.write('\nГруппы: Нет')
            
            # Индивидуальные разрешения
            user_perms = user.user_permissions.all()
            if user_perms:
                self.stdout.write(f'\nИндивидуальные разрешения ({user_perms.count()}):')
                for perm in user_perms:
                    self.stdout.write(f'  • {perm.name} ({perm.codename})')
            else:
                self.stdout.write('\nИндивидуальные разрешения: Нет')
            
            # Все эффективные разрешения
            all_perms = user.get_all_permissions()
            if all_perms:
                self.stdout.write(f'\nВсе эффективные разрешения ({len(all_perms)}):')
                for perm in sorted(all_perms):
                    self.stdout.write(f'  • {perm}')
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Пользователь "{username}" не найден')
            )

    def show_group_permissions(self, group_name):
        """Показать разрешения группы"""
        try:
            group = Group.objects.get(name=group_name)
            self.stdout.write(
                self.style.SUCCESS(f'\n=== Разрешения группы: {group.name} ===')
            )
            
            permissions = group.permissions.all()
            users = group.user_set.all()
            
            self.stdout.write(f'Пользователей в группе: {users.count()}')
            if users:
                for user in users:
                    self.stdout.write(f'  • {user.username} ({user.get_full_name() or "Без имени"})')
            
            self.stdout.write(f'\nРазрешения ({permissions.count()}):')
            if permissions:
                for perm in permissions:
                    self.stdout.write(f'  • {perm.name}')
                    self.stdout.write(f'    Код: {perm.codename}')
                    self.stdout.write(f'    Модель: {perm.content_type}')
            else:
                self.stdout.write('  Нет разрешений')
                
        except Group.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Группа "{group_name}" не найдена')
            )

    def show_all_permissions(self, custom_only=False):
        """Показать все разрешения в системе"""
        self.stdout.write(
            self.style.SUCCESS('\n=== Все разрешения в системе ===')
        )
        
        # Пользовательские разрешения
        custom_codenames = [
            'can_publish_photos', 'can_feature_photos', 'can_moderate_comments',
            'can_view_all_profiles', 'can_edit_any_profile', 'can_upload_unlimited',
            'can_manage_user_roles'
        ]
        
        if custom_only:
            permissions = Permission.objects.filter(codename__in=custom_codenames)
            self.stdout.write('\n--- ПОЛЬЗОВАТЕЛЬСКИЕ РАЗРЕШЕНИЯ ---')
        else:
            permissions = Permission.objects.all()
            self.stdout.write('\n--- ВСЕ РАЗРЕШЕНИЯ ---')
        
        # Группируем по приложениям
        apps = {}
        for perm in permissions:
            app_label = perm.content_type.app_label
            if app_label not in apps:
                apps[app_label] = {}
            
            model = perm.content_type.model
            if model not in apps[app_label]:
                apps[app_label][model] = []
            
            is_custom = perm.codename in custom_codenames
            apps[app_label][model].append((perm, is_custom))
        
        for app_label, models in apps.items():
            self.stdout.write(f'\n{app_label.upper()}:')
            for model, perms in models.items():
                self.stdout.write(f'  {model}:')
                for perm, is_custom in perms:
                    marker = ' [CUSTOM]' if is_custom else ''
                    self.stdout.write(f'    • {perm.name}{marker}')
                    self.stdout.write(f'      Код: {perm.codename}')
        
        # Статистика групп
        self.stdout.write(
            self.style.SUCCESS('\n=== Статистика групп ===')
        )
        groups = Group.objects.all()
        for group in groups:
            users_count = group.user_set.count()
            perms_count = group.permissions.count()
            self.stdout.write(
                f'{group.name}: {users_count} пользователей, {perms_count} разрешений'
            )
        
        # Статистика пользователей
        self.stdout.write(
            self.style.SUCCESS('\n=== Статистика пользователей ===')
        )
        total_users = User.objects.count()
        users_with_groups = User.objects.filter(groups__isnull=False).distinct().count()
        users_with_perms = User.objects.filter(user_permissions__isnull=False).distinct().count()
        superusers = User.objects.filter(is_superuser=True).count()
        staff = User.objects.filter(is_staff=True).count()
        
        self.stdout.write(f'Всего пользователей: {total_users}')
        self.stdout.write(f'Пользователей в группах: {users_with_groups}')
        self.stdout.write(f'Пользователей с индивидуальными разрешениями: {users_with_perms}')
        self.stdout.write(f'Суперпользователей: {superusers}')
        self.stdout.write(f'Персонала: {staff}')