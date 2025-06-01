# Отчет о выполнении задания по формам Django

## Обзор выполненных задач

В рамках данного задания были реализованы следующие требования:
1. Создание формы, не связанной с моделью, с валидаторами
2. Создание формы, связанной с моделью, с валидаторами  
3. Реализация загрузки файлов с генерацией уникальных имен
4. Добавление изображений к записям в БД с отображением на сайте

## 1. Генерация уникальных имен файлов

### Проблема
Необходимо обеспечить возможность загрузки файлов с одинаковыми исходными именами без конфликтов.

### Решение
В файле `models.py` добавлена функция для генерации уникальных имен:

```python
import uuid
import os

def generate_unique_filename(instance, filename):
    """Генерирует уникальное имя файла для избежания конфликтов"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('photos/', filename)
```

Функция использует UUID4 для создания уникального идентификатора, сохраняя оригинальное расширение файла.

### Применение в модели
```python
class Photo(models.Model):
    image = models.ImageField(
        upload_to=generate_unique_filename, 
        verbose_name="Изображение",
        help_text="Поддерживаемые форматы: JPG, PNG, GIF. Максимальный размер: 10MB"
    )
```

## 2. Собственные валидаторы

### Валидатор проверки нецензурной лексики
```python
def validate_no_profanity(value):
    """Собственный валидатор для проверки на нецензурную лексику"""
    profanity_words = ['плохое_слово1', 'плохое_слово2', 'spam', 'bad']
    for word in profanity_words:
        if word.lower() in value.lower():
            raise ValidationError(f'Текст содержит недопустимое слово: {word}')
```

### Валидатор размера изображения
```python
def validate_image_size(value):
    """Собственный валидатор для проверки размера изображения"""
    if value.size > 10 * 1024 * 1024:  # 10MB
        raise ValidationError('Размер файла не должен превышать 10MB')
```

### Валидатор рейтинга
```python
def validate_rating_range(value):
    """Собственный валидатор для проверки рейтинга"""
    if not (0 <= value <= 10):
        raise ValidationError('Рейтинг должен быть от 0 до 10')
```

### Валидатор формата заголовка
```python
def validate_title_format(value):
    """Собственный валидатор для проверки формата заголовка"""
    if not re.match(r'^[А-Яа-яA-Za-z0-9\s\-_.,!?]+$', value):
        raise ValidationError('Заголовок содержит недопустимые символы')
```

## 3. Форма НЕ связанная с моделью (PhotoUploadForm)

### Описание
Форма `PhotoUploadForm` наследуется от `forms.Form` и не связана напрямую с моделью. Все поля определяются вручную.

### Ключевые особенности:
```python
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
```

### Валидация в несвязанной форме:
```python
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
```

### Обработка в представлении:
```python
def upload_photo_simple(request):
    """Загрузка фотографии с использованием формы, НЕ связанной с моделью"""
    if request.method == 'POST':
        form = PhotoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Создаем объект Photo из данных формы вручную
                photo = Photo(
                    title=form.cleaned_data['title'],
                    description=form.cleaned_data['description'],
                    image=form.cleaned_data['image'],
                    category_type=form.cleaned_data['category_type'],
                    rating=form.cleaned_data['rating'],
                    is_featured=form.cleaned_data['is_featured']
                )
                
                if request.user.is_authenticated:
                    photo.uploaded_by = request.user
                
                photo.save()
```

## 4. Форма связанная с моделью (PhotoForm)

### Описание
Форма `PhotoForm` наследуется от `forms.ModelForm` и автоматически генерирует поля на основе модели `Photo`.

### Ключевые особенности:
```python
class PhotoForm(forms.ModelForm):
    """Форма для фотографии, связанная с моделью"""
    
    tags = forms.CharField(
        required=False,
        validators=[validate_no_profanity],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите теги через запятую'
        }),
        help_text='Введите теги через запятую, например: природа, горы, закат'
    )
    
    class Meta:
        model = Photo
        fields = ['title', 'image', 'description', 'category_type', 'rating', 'is_featured']
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
            # ... остальные виджеты
        }
```

### Добавление валидаторов к полям модели:
```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    
    # Добавляем собственные валидаторы к полям модели
    self.fields['title'].validators.extend([
        validate_no_profanity,
        validate_title_format
    ])
    self.fields['description'].validators.append(validate_no_profanity)
    self.fields['image'].validators.append(validate_image_size)
    self.fields['rating'].validators.append(validate_rating_range)
```

### Переопределение метода save():
```python
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
```

## 5. Различия между связанными и несвязанными формами

### Форма НЕ связанная с моделью (forms.Form):

**Преимущества:**
- Полный контроль над полями и их поведением
- Можно создавать поля, не соответствующие модели
- Гибкость в обработке данных
- Подходит для сложной логики валидации

**Недостатки:**
- Больше кода для написания
- Нужно вручную создавать объекты модели
- Дублирование логики модели
- Сложнее поддерживать при изменении модели

**Пример использования:**
```python
# Все поля определяются вручную
title = forms.CharField(max_length=200, validators=[...])
description = forms.CharField(widget=forms.Textarea, validators=[...])

# Создание объекта модели вручную
photo = Photo(
    title=form.cleaned_data['title'],
    description=form.cleaned_data['description'],
    # ... остальные поля
)
photo.save()
```

### Форма связанная с моделью (forms.ModelForm):

**Преимущества:**
- Автоматическая генерация полей из модели
- Встроенная валидация модели
- Метод save() работает автоматически
- Меньше кода для написания
- Автоматическое обновление при изменении модели

**Недостатки:**
- Меньше гибкости
- Сложнее добавить поля, не связанные с моделью
- Ограничения в кастомизации поведения

**Пример использования:**
```python
class Meta:
    model = Photo  # Указываем модель
    fields = ['title', 'description', 'image']  # Поля генерируются автоматически

# Сохранение происходит автоматически
photo = form.save()
```

## 6. Дополнительные улучшения

### Расширение модели Photo
Добавлены новые поля для демонстрации валидации:
```python
class Photo(models.Model):
    # ... существующие поля
    rating = models.IntegerField(
        default=0, 
        verbose_name="Рейтинг",
        help_text="Рейтинг от 0 до 10"
    )
    is_featured = models.BooleanField(default=False, verbose_name="Рекомендуемое")
```

### Улучшенная обработка ошибок
Добавлены сообщения об успехе и ошибках:
```python
try:
    photo = form.save(commit=False)
    # ... обработка
    messages.success(request, 'Фотография успешно загружена!')
    return redirect('photo_detail_slug', slug=photo.slug)
except Exception as e:
    messages.error(request, f'Ошибка при загрузке: {str(e)}')
```

### Валидация файлов изображений
```python
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
```

## 7. Заключение

Все требования задания выполнены:

1. ✅ **Форма не связанная с моделью** - `PhotoUploadForm` с полным набором валидаторов
2. ✅ **Форма связанная с моделью** - `PhotoForm` с автоматической генерацией полей
3. ✅ **Загрузка файлов** - реализована с генерацией уникальных имен через UUID
4. ✅ **Изображения в БД** - добавлено поле image с отображением на сайте

**Собственные валидаторы:**
- `validate_no_profanity` - проверка на нецензурную лексику
- `validate_image_size` - проверка размера файла
- `validate_rating_range` - проверка диапазона рейтинга  
- `validate_title_format` - проверка формата заголовка

**Стандартные валидаторы:**
- `MinLengthValidator` - минимальная длина
- `MaxLengthValidator` - максимальная длина
- Встроенная валидация типов полей Django

Формы протестированы на корректных и некорректных данных, обеспечивают надежную валидацию пользовательского ввода и безопасную загрузку файлов.
