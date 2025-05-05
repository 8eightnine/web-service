from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db.models import Count, F, Q, Value, Avg
from django.utils import timezone
from django.db.models.functions import Concat

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    slug = models.SlugField(unique=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def photo_count(self):
        return self.photos.count()

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def photo_count(self):
        return self.photos.count()

class Photo(models.Model):
    CATEGORY_CHOICES = [
        ('nature', 'Природа'),
        ('people', 'Люди'),
        ('architecture', 'Архитектура'),
        ('other', 'Другое'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photos', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='photos')
    category_type = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    tags = models.ManyToManyField(Tag, related_name='photos', blank=True)
    views = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    @classmethod
    def get_popular_photos(cls, limit=5):
        return cls.objects.annotate(
            comment_count=Count('comments')
        ).order_by('-views', '-comment_count')[:limit]
    
    @classmethod
    def get_photos_by_tag(cls, tag_slug):
        return cls.objects.filter(tags__slug=tag_slug)
    
    @classmethod
    def get_photos_with_stats(cls):
        return cls.objects.annotate(
            comment_count=Count('comments', distinct=True),
            tag_count=Count('tags', distinct=True),
            days_since_upload=F('uploaded_at') - Value(timezone.now().date())
        )

class Comment(models.Model):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.photo.title}"

class PhotoCategory(models.Model):
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ('photo', 'category')
