from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator, MaxLengthValidator
from .models import Photo, Category, Comment, PhotoCategory
import re


def validate_no_profanity(value):
    """Собственный валидатор для проверки на нецензурную лексику"""
    profanity_words = ['плохое_слово1', 'плохое_слово2', 'spam', 'bad']
    for word in profanity_words:
        if word.lower() in value.lower():
            raise ValidationError(f'Текст содержит недопустимое слово: {word}')

def validate_image_size(value):
    """Собственный валидатор для проверки размера изображения"""
    if value.size > 10 * 1024 * 1024:  # 10MB
        raise ValidationError('Размер файла не должен превышать 10MB')

def validate_title_format(value):
    """Собственный валидатор для проверки формата заголовка"""
    if not re.match(r'^[А-Яа-яA-Za-z0-9\s\-_.,!?]+$', value):
        raise ValidationError('Заголовок содержит недопустимые символы')


# 1. Форма НЕ связанная с моделью
class PhotoUploadForm(forms.Form):
    """Форма для загрузки фотографии, не связанная с моделью"""
    
    title = forms.CharField(
        max_length=200,
        min_length=3,
        validators=[
            MinLengthValidator(3, message="Заголовок должен содержать минимум 3 символа"),
            MaxLengthValidator(200, message="Заголовок не должен превышать 200 символов"),
            validate_no_profanity,
            validate_title_format
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите заголовок фотографии'
        }),
        label="Заголовок",
        help_text="От 3 до 200 символов, без нецензурной лексики"
    )
    
    description = forms.CharField(
        validators=[
            MinLengthValidator(10, message="Описание должно содержать минимум 10 символов"),
            validate_no_profanity
        ],
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Опишите вашу фотографию'
        }),
        label="Описание",
    )
    
    image = forms.ImageField(
        validators=[validate_image_size],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
        }),
        label="Изображение",
        help_text="Поддерживаемые форматы: JPG, PNG, GIF. Максимум 10MB"
    )
    
    category_type = forms.ChoiceField(
        choices=PhotoCategory.choices(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Категория"
    )
    
    tags = forms.CharField(
        required=False,
        validators=[validate_no_profanity],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'природа, горы, закат'
        }),
        label="Теги",
        help_text="Введите теги через запятую"
    )

    def clean_title(self):
        """Дополнительная валидация заголовка"""
        title = self.cleaned_data.get('title')
        if title and len(title.strip()) < 3:
            raise ValidationError('Заголовок после удаления пробелов слишком короткий')
        return title.strip() if title else title

    def clean_tags(self):
        """Валидация тегов"""
        tags = self.cleaned_data.get('tags', '')
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
            if len(tag_list) > 10:
                raise ValidationError('Максимум 10 тегов')
            for tag in tag_list:
                if len(tag) > 50:
                    raise ValidationError('Каждый тег не должен превышать 50 символов')
        return tags

# 2. Форма связанная с моделью
class PhotoForm(forms.ModelForm):
    """Форма для фотографии, связанная с моделью"""
    
    tags = forms.CharField(
        required=False,
        validators=[validate_no_profanity],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите теги через запятую'
        }),
        label="Теги",
        help_text='Введите теги через запятую, например: природа, горы, закат'
    )
    
    class Meta:
        model = Photo
        fields = ['title', 'image', 'description', 'category_type']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите заголовок'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Опишите вашу фотографию'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'category_type': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Добавляем собственные валидаторы к полям модели
        self.fields['title'].validators.extend([
            validate_no_profanity,
            validate_title_format
        ])
        self.fields['description'].validators.append(validate_no_profanity)
        self.fields['image'].validators.append(validate_image_size)
        
        # Если редактируем существующую фотографию, заполняем теги
        if self.instance.pk:
            self.initial['tags'] = ', '.join([tag.name for tag in self.instance.tags.all()])

    def clean_title(self):
        """Дополнительная валидация заголовка"""
        title = self.cleaned_data.get('title')
        if title and len(title.strip()) < 3:
            raise ValidationError('Заголовок после удаления пробелов слишком короткий')
        return title.strip() if title else title

    def clean_tags(self):
        """Валидация тегов"""
        tags = self.cleaned_data.get('tags', '')
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
            if len(tag_list) > 10:
                raise ValidationError('Максимум 10 тегов')
            for tag in tag_list:
                if len(tag) > 50:
                    raise ValidationError('Каждый тег не должен превышать 50 символов')
        return tags

    def clean_image(self):
        """Дополнительная валидация изображения"""
        image = self.cleaned_data.get('image')
        if image:
            # Проверяем тип файла
            if not image.content_type.startswith('image/'):
                raise ValidationError('Файл должен быть изображением')
            
            # Проверяем расширение
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            if not any(image.name.lower().endswith(ext) for ext in allowed_extensions):
                raise ValidationError('Поддерживаемые форматы: JPG, PNG, GIF')
        
        return image

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if commit:
            instance.save()
            
            # Обработка тегов с taggit
            if 'tags' in self.cleaned_data:
                instance.tags.clear()
                
                tag_string = self.cleaned_data['tags']
                if tag_string:
                    tag_list = [tag.strip() for tag in tag_string.split(',') if tag.strip()]
                    instance.tags.add(*tag_list)
        
        return instance

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].validators.append(validate_no_profanity)
        self.fields['description'].validators.append(validate_no_profanity)

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Введите ваш комментарий...',
                'required': True
            })
        }
        labels = {
            'text': 'Комментарий'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].validators.extend([
            MinLengthValidator(5, message="Комментарий должен содержать минимум 5 символов"),
            validate_no_profanity
        ])

    def clean_text(self):
        """Дополнительная валидация текста комментария"""
        text = self.cleaned_data.get('text')
        if text and len(text.strip()) < 5:
            raise ValidationError('Комментарий после удаления пробелов слишком короткий')
        return text.strip() if text else text
