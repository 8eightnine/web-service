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

class PhotoManager(models.Manager):
    def get_by_category(self, category):
        return self.filter(category=category)
    
    def get_recent(self, count=5):
        return self.order_by('-uploaded_at')[:count]
    
    def get_by_user(self, user):
        return self.filter(uploaded_by=user)

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
