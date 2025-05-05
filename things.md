1. Создание таблицы БД и заполнение записями с помощью фреймворка
Для создания таблицы базы данных я использовал Django ORM. Сначала я определил модель Photo в файле photos/models.py:
```
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from enum import Enum

class PhotoCategory(Enum):
    NATURE = "Природа"
    PEOPLE = "Люди"
    ARCHITECTURE = "Архитектура"
    ANIMALS = "Животные"
    OTHER = "Другое"
    
    @classmethod
    def choices(cls):
        return [(item.name, item.value) for item in cls]

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name

class Photo(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    image = models.ImageField(upload_to='photos/')
    description = models.TextField()
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='photos')
    category_type = models.CharField(
        max_length=20,
        choices=PhotoCategory.choices(),
        default=PhotoCategory.OTHER.name
    )
    
    objects = models.Manager()  # Default manager
    custom = PhotoManager()     # Custom manager
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            if not base_slug:  # Если slugify вернул пустую строку для кириллицы
                # Используем транслитерацию или ID
                base_slug = f"photo-{self.pk or 'new'}"
        
            # Проверяем уникальность слага
            counter = 0
            slug = base_slug
            while Photo.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"
        
            self.slug = slug
    
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
```



Затем я создал миграции и применил их:
```
python manage.py makemigrations
python manage.py migrate
```

Для заполнения таблицы данными я создал форму для загрузки фотографий в photos/forms.py:
```
from django import forms
from .models import Photo, Category, PhotoCategory

class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['title', 'image', 'description', 'category', 'category_type']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category_type'].choices = PhotoCategory.choices()
```



И представление для обработки загрузки в photos/views.py:
```
def upload_photo(request):
    if request.method == 'POST':
        form = PhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            if request.user.is_authenticated:
                photo.uploaded_by = request.user
            photo.save()
            return redirect('photo_detail_slug', slug=photo.slug)
    else:
        form = PhotoForm()
    return render(request, 'photos/upload_photo.html', {'form': form})
```



2. Проверка данных в БД с помощью SQLiteStudio
После загрузки нескольких фотографий через веб-интерфейс, я открыл базу данных с помощью SQLiteStudio и проверил таблицу photos_photo. В таблице появились записи с загруженными фотографиями, их заголовками, описаниями, слагами и другими полями.

3. Наполнение страницы информацией из базы данных
Для отображения фотографий из базы данных я создал представление photo_list в photos/views.py:
```
def photo_list(request):
    sort_by = request.GET.get('sort', '-uploaded_at')
    category_filter = request.GET.get('category', None)
    
    photos = Photo.objects.all()
    
    # Apply filtering
    if category_filter:
        photos = photos.filter(category__slug=category_filter)
    
    # Apply sorting
    photos = photos.order_by(sort_by)
    
    # Get unique years
    years = Photo.objects.dates('uploaded_at',
                                'year').values_list('uploaded_at__year',
                                                    flat=True)
    
    # Get all categories for filter
    categories = Category.objects.all()
    
    return render(request, 'photos/photo_list.html', {
        'photos': photos,
        'years': years,
        'categories': categories,
        'current_category': category_filter,
        'current_sort': sort_by
    })
```



И шаблон photos/templates/photos/photo_list.html для отображения:
```
{% extends 'base.html' %}
{% load photo_filters %}

{% block title %}Фотографии{% endblock %}

{% block content %}
<div class="filters-container">
    <div class="filters-row">
        <div class="filter-group">
            <h3>Фильтр по годам</h3>
            <div class="filter-dropdown">
                <select id="year-filter" onchange="filterByYear(this.value)">
                    <option value="">Все годы</option>
                    {% for year in years %}
                        <option value="{{ year }}">{{ year }}</option>
                    {% endfor %}
                </select>
            </div>
        </div>
        
        <div class="filter-group">
            <h3>Фильтр по категориям</h3>
            <div class="filter-dropdown">
                <select id="category-filter" onchange="filterByCategory(this.value)">
                    <option value="">Все категории</option>
                    {% for category in categories %}
                        <option value="{{ category.slug }}" {% if current_category == category.slug %}selected{% endif %}>{{ category.name }}</option>
                    {% endfor %}
                </select>
            </div>
        </div>
        
        <div class="filter-group">
            <h3>Сортировка</h3>
            <div class="filter-dropdown">
                <select id="sort-filter" onchange="sortPhotos(this.value)">
                    <option value="title" {% if current_sort == 'title' %}selected{% endif %}>По названию (А-Я)</option>
                    <option value="-title" {% if current_sort == '-title' %}selected{% endif %}>По названию (Я-А)</option>
                    <option value="-uploaded_at" {% if current_sort == '-uploaded_at' %}selected{% endif %}>Сначала новые</option>
                    <option value="uploaded_at" {% if current_sort == 'uploaded_at' %}selected{% endif %}>Сначала старые</option>
                </select>
            </div>
        </div>
    </div>
</div>

<div class="photo-grid">
    {% for photo in photos %}
    <a href="{% if photo.slug %}{% url 'photo_detail_slug' photo.slug %}{% else %}{% url 'photo_detail' photo.pk %}{% endif %}" class="photo-card-link">
            <div class="photo-card">
                <h2>{{ photo.title|truncate_title }}</h2>
                <img src="{{ photo.image.url }}" alt="{{ photo.title }}">
                <p>{{ photo.description|truncatechars:20}}</p>
                <p class="photo-meta">
                    Категория: {{ photo.get_category_type_display }}
                    <br>
                    Загружено: {{ photo.uploaded_at|time_since_upload }}
                    {% if photo.uploaded_by %}
                        пользователем {{ photo.uploaded_by.username }}
                    {% else %}
                        анонимно
                    {% endif %}
                </p>
                {% if user.is_authenticated and photo.uploaded_by == user %}
                <div class="photo-actions">
                    <a href="{% url 'edit_photo' photo.slug %}" class="edit-btn">Редактировать</a>
                    <a href="{% url 'delete_photo' photo.slug %}" class="delete-btn">Удалить</a>
                </div>
                {% endif %}
            </div>
        </a>
    {% empty %}
        <p>Нет доступных фотографий.</p>
    {% endfor %}
</div>
{% endblock %}
```



4. Реализация CRUD-операций с записями БД
Создание (Create)
Создание новых записей реализовано через представление upload_photo, которое было описано выше.

Чтение (Read)
Для чтения отдельной записи я создал представление photo_detail:
```
def photo_detail(request, pk=None, slug=None):
    if pk:
        try:
            photo = Photo.objects.get(pk=pk)
        except Photo.DoesNotExist:
            raise Http404("Фотография не найдена")
    elif slug:
        try:
            photo = Photo.objects.get(slug=slug)
        except Photo.DoesNotExist:
            raise Http404("Фотография не найдена")
    else:
        raise Http404("Неверный запрос")
        
    return render(request, 'photos/photo_detail.html', {'photo': photo})
```



Обновление (Update)
Для обновления записей я создал представление edit_photo:
```
@login_required
def edit_photo(request, slug):
    photo = get_object_or_404(Photo, slug=slug)
    
    # Check if user is the owner
    if photo.uploaded_by != request.user and not request.user.is_staff:
        return redirect('photo_detail', slug=slug)
        
    if request.method == 'POST':
        form = PhotoForm(request.POST, request.FILES, instance=photo)
        if form.is_valid():
            form.save()
            return redirect('photo_detail', slug=photo.slug)
    else:
        form = PhotoForm(instance=photo)
    
    return render(request, 'photos/edit_photo.html', {
        'form': form,
        'photo': photo
    })
```



Удаление (Delete)
Для удаления записей я создал представление delete_photo:
```
@login_required
def delete_photo(request, slug):
    photo = get_object_or_404(Photo, slug=slug)
    
    # Check if user is the owner
    if photo.uploaded_by != request.user and not request.user.is_staff:
        return redirect('photo_detail', slug=slug)
        
    if request.method == 'POST':
        photo.delete()
        return redirect('photo_list')
        
    return render(request, 'photos/delete_photo.html', {'photo': photo})
```



Фильтрация
Фильтрация реализована в представлении photo_list (по категориям) и в представлении photos_by_year:
```
def photos_by_year(request, year):
    photos = Photo.objects.filter(uploaded_at__year=year)
    years = Photo.objects.dates('uploaded_at',
                                'year').values_list('uploaded_at__year',
                                                    flat=True)
    return render(request, 'photos/photos_by_year.html', {
        'photos': photos,
        'year': year,
        'years': years
    })
```



Также реализована фильтрация по категориям:
```
def photos_by_category(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    photos = Photo.objects.filter(category=category)
    
    return render(request, 'photos/photos_by_category.html', {
        'photos': photos,
        'category': category
    })
```



Сортировка
Сортировка реализована в представлении photo_list с помощью параметра sort_by:
```
sort_by = request.GET.get('sort', '-uploaded_at')
photos = photos.order_by(sort_by)
```



5. Добавление слагов и отображение записей по слагам
Я добавил поле slug в модель Photo и реализовал автоматическую генерацию слагов в методе save:
```
def save(self, *args, **kwargs):
    if not self.slug:
        base_slug = slugify(self.title)
        if not base_slug:  # Если slugify вернул пустую строку для кириллицы
            # Используем транслитерацию или ID
            base_slug = f"photo-{self.pk or 'new'}"
    
        # Проверяем уникальность слага
        counter = 0
        slug = base_slug
        while Photo.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            counter += 1
            slug = f"{base_slug}-{counter}"
    
        self.slug = slug

    super().save(*args, **kwargs)
```



Затем я добавил URL-маршрут для доступа к фотографиям по слагу:
```
path('photo/<slug:slug>/', views.photo_detail, name='photo_detail_slug'),
```



И обновил представление photo_detail, чтобы оно могло получать фотографии как по ID, так и по слагу:
```
def photo_detail(request, pk=None, slug=None):
    if pk:
        try:
            photo = Photo.objects.get(pk=pk)
        except Photo.DoesNotExist:
            raise Http404("Фотография не найдена")
    elif slug:
        try:
            photo = Photo.objects.get(slug=slug)
        except Photo.DoesNotExist:
            raise Http404("Фотография не найдена")
    else:
        raise Http404("Неверный запрос")
        
    return render(request, 'photos/photo_detail.html', {'photo': photo})
```
6. Создание пользовательского менеджера модели
Я создал пользовательский менеджер модели PhotoManager в файле photos/models.py:
```
class PhotoManager(models.Manager):
    def get_by_category(self, category):
        return self.filter(category=category)
    
    def get_recent(self, count=5):
        return self.order_by('-uploaded_at')[:count]
    
    def get_by_user(self, user):
        return self.filter(uploaded_by=user)
```



Затем я добавил этот менеджер к модели Photo:
```
class Photo(models.Model):
    # ... поля модели ...
    
    objects = models.Manager()  # Стандартный менеджер
    custom = PhotoManager()     # Пользовательский менеджер
```



Использование пользовательского менеджера в представлении home:
```
def home(request):
    # Using custom manager to get recent photos
    recent_photos = Photo.custom.get_recent(5)
    return render(request, 'photos/home.html', {'recent_photos': recent_photos})
```



7. Использование класса перечисления
Я использовал класс перечисления Enum из стандартной библиотеки Python для создания перечисления PhotoCategory:
```
from enum import Enum

class PhotoCategory(Enum):
    NATURE = "Природа"
    PEOPLE = "Люди"
    ARCHITECTURE = "Архитектура"
    ANIMALS = "Животные"
    OTHER = "Другое"
    
    @classmethod
    def choices(cls):
        return [(item.name, item.value) for item in cls]
```



Затем я использовал это перечисление для определения поля category_type в модели Photo:
```
category_type = models.CharField(
    max_length=20,
    choices=PhotoCategory.choices(),
    default=PhotoCategory.OTHER.name
)
```



И в форме PhotoForm:
```
class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['title', 'image', 'description', 'category', 'category_type']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category_type'].choices = PhotoCategory.choices()
```



В шаблоне я использовал метод get_category_type_display() для отображения читаемого значения категории:
```
Категория: {{ photo.get_category_type_display }}
```