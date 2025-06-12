from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from users.models import Profile
from photos.models import Photo


class Command(BaseCommand):
    help = 'Настройка групп разрешений и пользователей'

    def handle(self, *args, **options):
        self.stdout.write('Начинаем настройку разрешений...')
        
        # Создаем группы
        self.create_groups()
        
        # Создаем пользовательские разрешения
        self.create_custom_permissions()
        
        # Создаем тестовых пользователей
        self.create_test_users()
        
        # Назначаем разрешения
        self.assign_permissions()
        
        self.stdout.write(
            self.style.SUCCESS('Настройка разрешений завершена успешно!')
        )

    def create_groups(self):
        """Создание групп разрешений"""
        self.stdout.write('Создаем группы...')
        
        # Группа модераторов
        moderators_group, created = Group.objects.get_or_create(name='Модераторы')
        if created:
            self.stdout.write(f'  ✓ Создана группа: {moderators_group.name}')
        
        # Группа редакторов
        editors_group, created = Group.objects.get_or_create(name='Редакторы')
        if created:
            self.stdout.write(f'  ✓ Создана группа: {editors_group.name}')
        
        # Группа VIP пользователей
        vip_group, created = Group.objects.get_or_create(name='VIP Пользователи')
        if created:
            self.stdout.write(f'  ✓ Создана группа: {vip_group.name}')

        # Назначаем разрешения группам
        self.assign_group_permissions()

    def create_custom_permissions(self):
        """Создание пользовательских разрешений"""
        self.stdout.write('Создаем пользовательские разрешения...')
        
        # Получаем ContentType для модели Profile
        profile_content_type = ContentType.objects.get_for_model(Profile)
        photo_content_type = ContentType.objects.get_for_model(Photo)
        
        # Создаем пользовательские разрешения
        custom_permissions = [
            {
                'codename': 'can_publish_photos',
                'name': 'Может публиковать фотографии без модерации',
                'content_type': photo_content_type
            },
            {
                'codename': 'can_feature_photos',
                'name': 'Может отмечать фотографии как рекомендуемые',
                'content_type': photo_content_type
            },
            {
                'codename': 'can_moderate_comments',
                'name': 'Может модерировать комментарии',
                'content_type': photo_content_type
            },
            {
                'codename': 'can_view_all_profiles',
                'name': 'Может просматривать все профили пользователей',
                'content_type': profile_content_type
            },
            {
                'codename': 'can_edit_any_profile',
                'name': 'Может редактировать любой профиль',
                'content_type': profile_content_type
            },
            {
                'codename': 'can_upload_unlimited',
                'name': 'Может загружать неограниченное количество фото',
                'content_type': photo_content_type
            }
        ]
        
        for perm_data in custom_permissions:
            permission, created = Permission.objects.get_or_create(
                codename=perm_data['codename'],
                defaults={
                    'name': perm_data['name'],
                    'content_type': perm_data['content_type']
                }
            )
            if created:
                self.stdout.write(f'  ✓ Создано разрешение: {permission.name}')

    def assign_group_permissions(self):
        """Назначение разрешений группам"""
        self.stdout.write('Назначаем разрешения группам...')
        
        # Получаем группы
        moderators = Group.objects.get(name='Модераторы')
        editors = Group.objects.get(name='Редакторы')
        vip_users = Group.objects.get(name='VIP Пользователи')
        
        # Разрешения для модераторов
        moderator_permissions = [
            'can_moderate_comments',
            'can_feature_photos',
            'can_view_all_profiles',
            'delete_photo',
            'change_photo',
        ]
        
        for perm_codename in moderator_permissions:
            try:
                permission = Permission.objects.get(codename=perm_codename)
                moderators.permissions.add(permission)
                self.stdout.write(f'  ✓ Модераторам добавлено: {permission.name}')
            except Permission.DoesNotExist:
                self.stdout.write(f'  ⚠ Разрешение не найдено: {perm_codename}')
        
        # Разрешения для редакторов
        editor_permissions = [
            'can_publish_photos',
            'can_feature_photos',
            'add_photo',
            'change_photo',
        ]
        
        for perm_codename in editor_permissions:
            try:
                permission = Permission.objects.get(codename=perm_codename)
                editors.permissions.add(permission)
                self.stdout.write(f'  ✓ Редакторам добавлено: {permission.name}')
            except Permission.DoesNotExist:
                self.stdout.write(f'  ⚠ Разрешение не найдено: {perm_codename}')
        
        # Разрешения для VIP пользователей
        vip_permissions = [
            'can_upload_unlimited',
            'can_publish_photos',
        ]
        
        for perm_codename in vip_permissions:
            try:
                permission = Permission.objects.get(codename=perm_codename)
                vip_users.permissions.add(permission)
                self.stdout.write(f'  ✓ VIP пользователям добавлено: {permission.name}')
            except Permission.DoesNotExist:
                self.stdout.write(f'  ⚠ Разрешение не найдено: {perm_codename}')

    def create_test_users(self):
        """Создание тестовых пользователей"""
        self.stdout.write('Создаем тестовых пользователей...')
        
        test_users = [
            {
                'username': 'moderator1',
                'email': 'moderator1@example.com',
                'first_name': 'Модератор',
                'last_name': 'Первый',
                'password': 'testpass123'
            },
            {
                'username': 'editor1',
                'email': 'editor1@example.com',
                'first_name': 'Редактор',
                'last_name': 'Первый',
                'password': 'testpass123'
            },
            {
                'username': 'vip_user1',
                'email': 'vip1@example.com',
                'first_name': 'VIP',
                'last_name': 'Пользователь',
                'password': 'testpass123'
            },
            {
                'username': 'regular_user1',
                'email': 'regular1@example.com',
                'first_name': 'Обычный',
                'last_name': 'Пользователь',
                'password': 'testpass123'
            },
            {
                'username': 'power_user1',
                'email': 'power1@example.com',
                'first_name': 'Продвинутый',
                'last_name': 'Пользователь',
                'password': 'testpass123'
            }
        ]
        
        for user_data in test_users:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                }
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(f'  ✓ Создан пользователь: {user.username}')

    def assign_permissions(self):
        """Назначение разрешений и групп пользователям"""
        self.stdout.write('Назначаем разрешения пользователям...')
        
        # Получаем группы
        moderators = Group.objects.get(name='Модераторы')
        editors = Group.objects.get(name='Редакторы')
        vip_users = Group.objects.get(name='VIP Пользователи')
        
        # Назначаем пользователей в группы
        try:
            moderator1 = User.objects.get(username='moderator1')
            moderator1.groups.add(moderators)
            self.stdout.write('  ✓ moderator1 добавлен в группу Модераторы')
        except User.DoesNotExist:
            pass
        
        try:
            editor1 = User.objects.get(username='editor1')
            editor1.groups.add(editors)
            self.stdout.write('  ✓ editor1 добавлен в группу Редакторы')
        except User.DoesNotExist:
            pass
        
        try:
            vip_user1 = User.objects.get(username='vip_user1')
            vip_user1.groups.add(vip_users)
            self.stdout.write('  ✓ vip_user1 добавлен в группу VIP Пользователи')
        except User.DoesNotExist:
            pass
        
        # Назначаем индивидуальные разрешения пользователю
        try:
            power_user1 = User.objects.get(username='power_user1')
            
            # Индивидуальные разрешения для продвинутого пользователя
            individual_permissions = [
                'can_edit_any_profile',
                'can_view_all_profiles',
                'add_photo',
                'change_photo',
            ]
            
            for perm_codename in individual_permissions:
                try:
                    permission = Permission.objects.get(codename=perm_codename)
                    power_user1.user_permissions.add(permission)
                    self.stdout.write(f'  ✓ power_user1 получил разрешение: {permission.name}')
                except Permission.DoesNotExist:
                    self.stdout.write(f'  ⚠ Разрешение не найдено: {perm_codename}')
                    
        except User.DoesNotExist:
            pass