from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Profile


class ProfileForm(forms.ModelForm):
    """
    Форма для редактирования профиля пользователя
    """
    
    class Meta:
        model = Profile
        fields = ['bio', 'avatar']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Расскажите о себе...'
            }),
            'avatar': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bio'].required = False
        self.fields['avatar'].required = False


class UserUpdateForm(forms.ModelForm):
    """
    Форма для обновления основной информации пользователя
    """
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Email',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class ProfileUserForm(forms.ModelForm):
    """
    Форма для редактирования профиля пользователя (используется в ProfileUser view)
    """
    username = forms.CharField(disabled=True, label='Логин', widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.CharField(disabled=True, label='E-mail', widget=forms.TextInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(label='Имя', widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label='Фамилия', widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Email',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Имя'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Фамилия'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = False
        self.fields['last_name'].required = False


class UserRegistrationForm(UserCreationForm):
    """
    Расширенная форма регистрации пользователя
    """
    email = forms.EmailField(
        required=True,
        label='Email адрес',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваш email'
        }),
        help_text='Обязательное поле. Введите действующий email адрес.'
    )
    
    first_name = forms.CharField(
        max_length=30,
        required=False,
        label='Имя',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваше имя'
        }),
        help_text='Необязательное поле.'
    )
    
    last_name = forms.CharField(
        max_length=30,
        required=False,
        label='Фамилия',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите вашу фамилию'
        }),
        help_text='Необязательное поле.'
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        labels = {
            'username': 'Имя пользователя',
        }
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите имя пользователя'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Обновляем labels для полей паролей
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Подтверждение пароля'
        
        # Настройка виджетов для полей паролей
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Повторите пароль'
        })
        
        # Убираем стандартный help_text для пароля, так как будем использовать динамический
        self.fields['username'].help_text = 'Обязательное поле. Не более 150 символов. Только буквы, цифры и символы @/./+/-/_.'
        self.fields['password1'].help_text = None  # Убираем стандартный help_text
        self.fields['password2'].help_text = 'Введите тот же пароль для подтверждения.'

    def clean_email(self):
        """Проверка уникальности email"""
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует.')
        return email

    def clean_username(self):
        """Проверка уникальности username"""
        username = self.cleaned_data.get('username')
        if username and User.objects.filter(username=username).exists():
            raise ValidationError('Пользователь с таким именем уже существует.')
        return username

    def save(self, commit=True):
        """Сохранение пользователя с дополнительными полями"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            with transaction.atomic():
                user.save()
                # Профиль создастся автоматически через сигнал
        return user


class CustomPasswordResetForm(PasswordResetForm):
    """
    Кастомная форма для сброса пароля с проверкой существования email
    """
    
    email = forms.EmailField(
        label='Email адрес',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите ваш email адрес',
            'autocomplete': 'email'
        }),
        help_text='Введите email адрес, который вы использовали при регистрации.'
    )

    def clean_email(self):
        """Проверка существования пользователя с указанным email"""
        email = self.cleaned_data.get('email')
        
        if email:
            # Проверяем, существует ли пользователь с таким email
            if not User.objects.filter(email=email).exists():
                raise ValidationError(
                    'Пользователь с таким email адресом не найден. '
                    'Проверьте правильность введенного адреса или зарегистрируйтесь.'
                )
        
        return email

    def get_users(self, email):
        """
        Возвращает активных пользователей с указанным email адресом
        """
        active_users = User.objects.filter(
            email__iexact=email,
            is_active=True
        )
        return (
            user for user in active_users
            if user.has_usable_password()
        )
