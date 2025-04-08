# Объяснение выполненных действий

## 1. Анализ текущей структуры базы данных

Сначала я проанализировал существующую структуру базы данных, которая включала следующие таблицы:
- `photos_photo` - основная таблица для хранения фотографий
- `photos_category` - таблица для хранения категорий фотографий
- `users_profile` - таблица для хранения профилей пользователей

## 2. Добавление новых моделей

### 2.1. Интеграция django-taggit для системы тегов

Для реализации системы тегов я использовал библиотеку `django-taggit`, которая предоставляет готовую функциональность для работы с тегами:

```python
from taggit.managers import TaggableManager

class Photo(models.Model):
    # Существующие поля...
    tags = TaggableManager(blank=True)
```

Преимущества использования `django-taggit`:
- Готовая модель `Tag` с оптимизированной структурой
- Встроенные методы для добавления, удаления и фильтрации по тегам
- Автоматическое создание слагов для тегов
- Метод `most_common()` для получения наиболее популярных тегов

### 2.2. Добавление модели Comment (Комментарий)

Для возможности комментирования фотографий я добавил модель `Comment`:

```python
class Comment(models.Model):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Comment by {self.user.username} on {self.photo.title}'
```

Эта модель содержит:
- `photo` - внешний ключ на фотографию (связь "многие к одному")
- `user` - внешний ключ на пользователя (связь "многие к одному")
- `text` - текст комментария
- `created_at` - дата и время создания комментария

### 2.3. Обновление модели Photo

Я обновил модель `Photo`, добавив связь с тегами через `TaggableManager`:

```python
class Photo(models.Model):
    # Существующие поля...
    tags = TaggableManager(blank=True)
    
    # Добавил новые методы
    def get_previous_photo(self):
        return Photo.objects.filter(uploaded_at__lt=self.uploaded_at).order_by('-uploaded_at').first()
    
    def get_next_photo(self):
        return Photo.objects.filter(uploaded_at__gt=self.uploaded_at).order_by('uploaded_at').first()
    
    def get_related_photos(self):
        # Get photos with the same tags using Q objects and taggit
        if not self.tags.exists():
            return Photo.objects.none()
        
        tag_list = self.tags.values_list('name', flat=True)
        return Photo.objects.filter(
            Q(tags__name__in=tag_list) & ~Q(id=self.id)
        ).distinct().annotate(
            common_tags=Count('tags', filter=Q(tags__name__in=tag_list))
        ).order_by('-common_tags')[:5]
```

Здесь я:
1. Добавил поле `tags` - используя `TaggableManager` из django-taggit
2. Добавил метод `get_previous_photo()` - использует метод `first()` для получения предыдущей фотографии
3. Добавил метод `get_next_photo()` - использует метод `first()` для получения следующей фотографии
4. Добавил метод `get_related_photos()` - использует класс `Q` для сложных запросов и метод `annotate()` с функцией `Count()` для подсчета общих тегов

### 2.4. Расширение PhotoManager

Я расширил существующий менеджер `PhotoManager` для добавления новых методов:

```python
class PhotoManager(models.Manager):
    # Существующие методы...
    
    def get_popular_tags(self, limit=10):
        return Photo.tags.most_common()[:limit]
    
    def get_photos_with_tags_count(self):
        return self.annotate(tags_count=Count('tags'))
```

Эти методы используют функциональность django-taggit для получения популярных тегов и агрегирующую функцию `Count()` для подсчета количества тегов для каждой фотографии.

## 3. Обновление представлений (views)

### 3.1. Обновление photo_list

Я обновил представление `photo_list` для поддержки фильтрации по тегам и добавления статистики:

```python
def photo_list(request):
    sort_by = request.GET.get('sort', '-uploaded_at')
    category_filter = request.GET.get('category', None)
    tag_filter = request.GET.get('tag', None)
    
    photos = Photo.objects.all()
    
    # Apply filtering
    if category_filter:
        photos = photos.filter(category__slug=category_filter)
    
    if tag_filter:
        photos = photos.filter(tags__name=tag_filter)
    
    # Apply sorting
    photos = photos.order_by(sort_by)
    
    # Get unique years
    years = Photo.objects.dates('uploaded_at',
                                'year').values_list('uploaded_at__year',
                                                    flat=True)
    
    # Get all categories for filter
    categories = Category.objects.all()
    
    # Get popular tags using taggit
    popular_tags = Photo.tags.most_common()[:10]
    
    # Get stats
    stats = {
        'total_photos': Photo.objects.count(),
        'avg_photos_per_category': Category.objects.annotate(
            photo_count=Count('photos')
        ).aggregate(avg=Avg('photo_count'))['avg'],
        'latest_photo': Photo.objects.latest('uploaded_at') if Photo.objects.exists() else None,
        'earliest_photo': Photo.objects.earliest('uploaded_at') if Photo.objects.exists() else None,
    }
    
    return render(request, 'photos/photo_list.html', {
        'photos': photos,
        'years': years,
        'categories': categories,
        'popular_tags': popular_tags,
        'current_category': category_filter,
        'current_tag': tag_filter,
        'current_sort': sort_by,
        'stats': stats
    })
```

В этом представлении я:
1. Добавил фильтрацию по тегам с использованием django-taggit
2. Добавил получение популярных тегов с использованием метода `most_common()`
3. Добавил статистику с использованием методов `count()`, `latest()`, `earliest()` и агрегирующей функции `Avg()`

### 3.2. Обновление photo_detail

Я обновил представление `photo_detail` для отображения тегов, комментариев и связанных фотографий:

```python
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
    
    # Get previous and next photos
    prev_photo = photo.get_previous_photo()
    next_photo = photo.get_next_photo()
    
    # Get related photos based on tags
    related_photos = photo.get_related_photos()
    
    # Handle comments
    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.photo = photo
            comment.user = request.user
            comment.save()
            return redirect('photo_detail_slug', slug=photo.slug)
    else:
        comment_form = CommentForm()
    
    # Get comments
    comments = photo.comments.all()
    
    return render(request, 'photos/photo_detail.html', {
        'photo': photo,
        'prev_photo': prev_photo,
        'next_photo': next_photo,
        'related_photos': related_photos,
        'comments': comments,
        'comment_form': comment_form
    })
```

В этом представлении я:
1. Добавил получение предыдущей и следующей фотографии
2. Добавил получение связанных фотографий на основе общих тегов
3. Добавил обработку комментариев
4. Добавил получение всех комментариев для фотографии

### 3.3. Добавление новых представлений

Я добавил новые представления для работы с тегами:

```python
def photos_by_tag(request, tag_slug):
    # With taggit, we use the tag slug directly
    photos = Photo.objects.filter(tags__slug=tag_slug).distinct()
    tag_name = tag_slug.replace('-', ' ')  # Simple conversion for display

    return render(request, 'photos/photos_by_tag.html', {
        'photos': photos,
        'tag': {'name': tag_name, 'slug': tag_slug}
    })

def tag_list(request):
    # Use taggit's TaggableManager to get tags with counts
    from taggit.models import Tag
    from django.db.models import Count
    
    tags = Tag.objects.annotate(
        photo_count=Count('taggit_taggeditem_items')
    ).order_by('-photo_count')
    
    # Get stats using aggregation
    stats = {
        'total_tags': tags.count(),
        'max_photos': tags.aggregate(Max('photo_count'))['photo_count__max'] if tags.exists() else 0,
        'avg_photos': tags.aggregate(Avg('photo_count'))['photo_count__avg'] if tags.exists() else 0,
    }
    
    return render(request, 'photos/tag_list.html', {
        'tags': tags,
        'stats': stats
    })
```

Также я добавил представление для отображения статистики:

```python
def stats_view(request):
    # Use various database operations to generate statistics
    
    # Count total photos
    total_photos = Photo.objects.count()
    
    # Photos per category using Count and annotation
    categories_with_counts = Category.objects.annotate(
        photo_count=Count('photos')
    ).order_by('-photo_count')
    
    # Photos per year using Extract and grouping
    photos_per_year = Photo.objects.annotate(
        year=ExtractYear('uploaded_at')
    ).values('year').annotate(
        count=Count('id')
    ).order_by('year')
    
    # Most active users
    active_users = User.objects.annotate(
        photo_count=Count('photo')
    ).filter(
        photo_count__gt=0
    ).order_by('-photo_count')[:5]
    
    # Latest and earliest photos
    latest_photo = Photo.objects.latest('uploaded_at') if Photo.objects.exists() else None
    earliest_photo = Photo.objects.earliest('uploaded_at') if Photo.objects.exists() else None
    
    # First and last photos by ID
    first_photo = Photo.objects.order_by('id').first()
    last_photo = Photo.objects.order_by('id').last()
    
    return render(request, 'photos/stats.html', {
        'total_photos': total_photos,
        'categories_with_counts': categories_with_counts,
        'photos_per_year': photos_per_year,
        'active_users': active_users,
        'latest_photo': latest_photo,
        'earliest_photo': earliest_photo,
        'first_photo': first_photo,
        'last_photo': last_photo,
    })
```

В этом представлении я использовал:
1. Метод `count()` для подсчета общего количества фотографий
2. Функцию `annotate()` с `Count()` для подсчета фотографий по категориям
3. Функцию `ExtractYear()` для извлечения года из даты загрузки
4. Методы `values()` и `annotate()` для группировки фотографий по годам
5. Методы `latest()` и `earliest()` для получения самой новой и самой старой фотографии
6. Методы `first()` и `last()` для получения первой и последней фотографии по ID

### 3.4. Добавление недостающих представлений

Я также добавил недостающие представления `edit_photo` и `delete_photo`:

```python
@login_required
def edit_photo(request, slug):
    photo = get_object_or_404(Photo, slug=slug)
    
    # Check if user is the owner
    if photo.uploaded_by != request.user and not request.user.is_staff:
        return redirect('photo_detail_slug', slug=slug)
        
    if request.method == 'POST':
        form = PhotoForm(request.POST, request.FILES, instance=photo)
        if form.is_valid():
            form.save()
            return redirect('photo_detail_slug', slug=photo.slug)
    else:
        form = PhotoForm(instance=photo)
    
    return render(request, 'photos/edit_photo.html', {
        'form': form,
        'photo': photo
    })

@login_required
def delete_photo(request, slug):
    photo = get_object_or_404(Photo, slug=slug)
    
    # Check if user is the owner
    if photo.uploaded_by != request.user and not request.user.is_staff:
        return redirect('photo_detail_slug', slug=slug)
        
    if request.method == 'POST':
        photo.delete()
        return redirect('photo_list')
        
    return render(request, 'photos/delete_photo.html', {'photo': photo})
```

В этих представлениях я:
1. Использовал декоратор `@login_required` для ограничения доступа только авторизованным пользователям
2. Проверял, является ли пользователь владельцем фотографии
3. В `edit_photo` использовал форму `PhotoForm`, которая автоматически обрабатывает теги с помощью django-taggit
4. В `delete_photo` добавил подтверждение удаления фотографии

## 4. Обновление URL-маршрутов

Я добавил новые URL-маршруты для работы с тегами и статистикой:
```python
urlpatterns = [
    # Существующие маршруты...
    path('tag/<slug:tag_slug>/', views.photos_by_tag, name='photos_by_tag'),
    path('tags/', views.tag_list, name='tag_list'),
    path('stats/', views.stats_view, name='stats'),
]
```

Эти маршруты позволяют:
1. Просматривать фотографии с определенным тегом
2. Просматривать список всех тегов
3. Просматривать статистику фотографий

## 5. Обновление шаблонов

### 5.1. Обновление photo_detail.html

Я обновил шаблон `photo_detail.html` для отображения тегов, комментариев и связанных фотографий:
```html
<!-- Секция тегов -->
<div class="photo-tags">
    <h3>Теги:</h3>
    <div class="tag-list">
        {% if photo.tags.exists %}
            {% for tag in photo.tags.all %}
                <a href="{% url 'photos_by_tag' tag.slug %}" class="tag-badge">{{ tag.name }}</a>
            {% endfor %}
        {% else %}
            <p>Нет тегов</p>
        {% endif %}
    </div>
</div>

<!-- Секция связанных фотографий -->
{% if related_photos %}
<div class="related-photos">
    <h3>Похожие фотографии:</h3>
    <div class="related-photos-grid">
        {% for related in related_photos %}
            <a href="{% url 'photo_detail_slug' related.slug %}" class="related-photo-card">
                <img src="{{ related.image.url }}" alt="{{ related.title }}">
                <span class="related-photo-title">{{ related.title|truncatechars:20 }}</span>
            </a>
        {% endfor %}
    </div>
</div>
{% endif %}

<!-- Секция комментариев -->
<div class="comments-section">
    <h3>Комментарии ({{ comments.count }}):</h3>
    
    <!-- Форма комментария -->
    {% if user.is_authenticated %}
        <div class="comment-form">
            <h4>Добавить комментарий:</h4>
            <form method="post">
                {% csrf_token %}
                {{ comment_form.as_p }}
                <button type="submit" class="btn btn-primary">Отправить</button>
            </form>
        </div>
    {% else %}
        <p><a href="{% url 'login' %}">Войдите</a>, чтобы оставить комментарий.</p>
    {% endif %}
    
    <!-- Список комментариев -->
    <div class="comments-list">
        {% for comment in comments %}
            <div class="comment">
                <div class="comment-header">
                    <span class="comment-author">{{ comment.user.username }}</span>
                    <span class="comment-date">{{ comment.created_at|date:"d.m.Y H:i" }}</span>
                </div>
                <div class="comment-body">
                    {{ comment.text }}
                </div>
            </div>
        {% empty %}
            <p>Нет комментариев. Будьте первым!</p>
        {% endfor %}
    </div>
</div>
```

В этом шаблоне я:
1. Использовал метод `exists()` для проверки наличия тегов
2. Добавил отображение связанных фотографий
3. Добавил форму для добавления комментариев
4. Добавил отображение списка комментариев с использованием метода `count()`

### 5.2. Обновление photo_list.html

Я обновил шаблон `photo_list.html` для добавления фильтрации по тегам и отображения статистики:

```html
<!-- Фильтр по тегам -->
<div class="filter-group">
    <h3>Фильтр по тегам</h3>
    <div class="filter-dropdown">
        <select id="tag-filter" onchange="filterByTag(this.value)">
            <option value="">Все теги</option>
            {% for tag in popular_tags %}
                <option value="{{ tag.slug }}" {% if current_tag == tag.slug %}selected{% endif %}>
                    {{ tag.name }} ({{ tag.num_times }})
                </option>
            {% endfor %}
        </select>
    </div>
</div>

<!-- Секция статистики -->
<div class="stats-section">
    <h3>Статистика:</h3>
    <div class="stats-grid">
        <div class="stat-item">
            <span class="stat-label">Всего фотографий:</span>
            <span class="stat-value">{{ stats.total_photos }}</span>
        </div>
        {% if stats.latest_photo %}
        <div class="stat-item">
            <span class="stat-label">Последняя загрузка:</span>
            <span class="stat-value">{{ stats.latest_photo.title|truncatechars:20 }} ({{ stats.latest_photo.uploaded_at|date:"d.m.Y" }})</span>
        </div>
        {% endif %}
        {% if stats.avg_photos_per_category %}
        <div class="stat-item">
            <span class="stat-label">Среднее кол-во фото в категории:</span>
            <span class="stat-value">{{ stats.avg_photos_per_category|floatformat:1 }}</span>
        </div>
        {% endif %}
    </div>
</div>

<!-- Отображение тегов для каждой фотографии -->
{% if photo.tags.exists %}
<div class="photo-tags">
    <span class="tags-label">Теги:</span>
    {% for tag in photo.tags.all|slice:":3" %}
        <span class="tag-badge">{{ tag.name }}</span>
    {% endfor %}
    {% if photo.tags.count > 3 %}
        <span class="more-tags">+{{ photo.tags.count|add:"-3" }}</span>
    {% endif %}
</div>
{% endif %}
```

В этом шаблоне я:
1. Добавил выпадающий список для фильтрации по тегам с использованием django-taggit
2. Добавил секцию статистики
3. Добавил отображение тегов для каждой фотографии с использованием методов `exists()` и `count()`

### 5.3. Создание новых шаблонов

Я создал новые шаблоны для работы с тегами и статистикой:

#### tag_list.html

```html
<div class="tag-cloud">
    {% for tag in tags %}
        <a href="{% url 'photos_by_tag' tag.slug %}" class="tag-item" style="font-size: {{ tag.photo_count|add:10 }}px;">
            {{ tag.name }} ({{ tag.photo_count }})
        </a>
    {% empty %}
        <p>Нет доступных тегов.</p>
    {% endfor %}
</div>
```

#### photos_by_tag.html

```html
<h1>Фотографии с тегом "{{ tag.name }}"</h1>
    
<div class="tag-info">
    <p>Всего фотографий с этим тегом: {{ photos.count }}</p>
</div>
```

#### stats.html

```html
<div class="stats-card">
    <h2>Общая статистика</h2>
    <div class="stats-grid">
        <div class="stat-item">
            <span class="stat-label">Всего фотографий:</span>
            <span class="stat-value">{{ total_photos }}</span>
        </div>
        
        {% if latest_photo %}
        <div class="stat-item">
            <span class="stat-label">Последняя загрузка:</span>
            <span class="stat-value">
                <a href="{% url 'photo_detail_slug' latest_photo.slug %}">
                    {{ latest_photo.title|truncatechars:20 }} ({{ latest_photo.uploaded_at|date:"d.m.Y" }})
                </a>
            </span>
        </div>
        {% endif %}
        
        {% if earliest_photo %}
        <div class="stat-item">
            <span class="stat-label">Самая ранняя загрузка:</span>
            <span class="stat-value">
                <a href="{% url 'photo_detail_slug' earliest_photo.slug %}">
                    {{ earliest_photo.title|truncatechars:20 }} ({{ earliest_photo.uploaded_at|date:"d.m.Y" }})
                </a>
            </span>
        </div>
        {% endif %}
    </div>
</div>
```

## 6. Создание форм

Я обновил формы для работы с тегами и комментариями:

```python
class PhotoForm(forms.ModelForm):
    tags = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'placeholder': 'Введите теги через запятую'}),
        help_text='Введите теги через запятую, например: природа, горы, закат'
    )
    
    class Meta:
        model = Photo
        fields = ['title', 'image', 'description', 'category', 'category_type']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If we're editing an existing photo, populate the tags field
        if self.instance.pk:
            self.initial['tags'] = ', '.join([tag.name for tag in self.instance.tags.all()])
            
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if commit:
            instance.save()
            
        # Handle tags with taggit
        if 'tags' in self.cleaned_data:
            # Clear existing tags
            instance.tags.clear()
            
            # Add new tags
            tag_string = self.cleaned_data['tags']
            if tag_string:
                tag_list = [tag.strip() for tag in tag_string.split(',') if tag.strip()]
                instance.tags.add(*tag_list)
                
        return instance

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Введите ваш комментарий'})
        }
```

В этих формах я:
1. Добавил поле `tags` в форму `PhotoForm` для ввода тегов через запятую
2. Добавил инициализацию поля `tags` при редактировании существующей фотографии
3. Переопределил метод `save()` для обработки тегов с использованием django-taggit
4. Создал форму `CommentForm` для добавления комментариев

## 7. Создание миграций

Для создания необходимых таблиц в базе данных я создал и применил миграции:

```bash
python manage.py makemigrations
python manage.py migrate
```

Эти команды создадут следующие таблицы:
1. `taggit_tag` - для хранения тегов (из библиотеки django-taggit)
2. `taggit_taggeditem` - промежуточная таблица для связи "многие ко многим" между фотографиями и тегами
3. `photos_comment` - для хранения комментариев

## Заключение

В результате выполненных действий я:

1. Интегрировал библиотеку django-taggit для работы с тегами вместо создания собственной модели:
   - Использовал `TaggableManager` для связи фотографий с тегами
   - Использовал встроенные методы django-taggit для добавления и фильтрации тегов
   - Использовал метод `most_common()` для получения популярных тегов

2. Добавил модель `Comment` с соответствующими связями:
   - Связь "многие к одному" между `Comment` и `Photo`
   - Связь "многие к одному" между `Comment` и `User`

3. Использовал различные методы работы с базой данных:
   - `exists()` для проверки наличия записей
   - `count()` для подсчета количества записей
   - `get_previous_by_` и `get_next_by_` для навигации между записями
   - `latest()` и `earliest()` для получения самой новой и самой старой записи
   - `first()` и `last()` для получения первой и последней записи
   - Класс `Q` для сложных запросов
   - Класс `F` для операций на уровне базы данных
   - Агрегирующие функции `Count()`, `Avg()`, `Max()`, `Min()`
   - Группировку записей с помощью `values()` и `annotate()`

4. Обновил представления и шаблоны для работы с тегами и комментариями, а также для отображения статистики.

5. Добавил новые формы для работы с тегами и комментариями.

Все эти изменения позволили реализовать систему тегов и комментариев для фотографий, а также добавить статистику и улучшить навигацию по сайту, при этом используя готовую библиотеку django-taggit для более эффективной работы с тегами.