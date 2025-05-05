from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from enum import Enum
from django.db.models import Count, F, Q, Value, ExpressionWrapper
from django.db.models.functions import ExtractYear
from taggit.managers import TaggableManager


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

    def get_popular_tags(self, limit=10):
        # Updated to work with taggit
        from django.db.models import Count
        return Photo.tags.most_common()[:limit]

    def get_photos_with_tags_count(self):
        return self.annotate(tags_count=Count('tags'))


class Category(models.Model):
    name = models.CharField(max_length=100)
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
    uploaded_by = models.ForeignKey(User,
                                    on_delete=models.SET_NULL,
                                    null=True,
                                    blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(Category,
                                 on_delete=models.SET_NULL,
                                 null=True,
                                 blank=True,
                                 related_name='photos')
    category_type = models.CharField(max_length=20,
                                     choices=PhotoCategory.choices(),
                                     default=PhotoCategory.OTHER.name)
    # Replace ManyToManyField with TaggableManager
    tags = TaggableManager(blank=True)

    objects = models.Manager()  # Default manager
    custom = PhotoManager()  # Custom manager

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

    def get_previous_photo(self):
        return Photo.objects.filter(
            uploaded_at__lt=self.uploaded_at).order_by('-uploaded_at').first()

    def get_next_photo(self):
        return Photo.objects.filter(
            uploaded_at__gt=self.uploaded_at).order_by('uploaded_at').first()

    def get_previous_by_category(self):
        if self.category:
            return self.get_previous_by_uploaded_at(category=self.category)
        return None

    def get_next_by_category(self):
        if self.category:
            return self.get_next_by_uploaded_at(category=self.category)
        return None

    def get_related_photos(self):
        # Get photos with the same tags using taggit
        if not self.tags.exists():
            return Photo.objects.none()

        tag_list = self.tags.values_list('name', flat=True)
        return Photo.objects.filter(tags__name__in=tag_list).exclude(
            id=self.id).distinct().annotate(
                common_tags=Count('tags', filter=Q(
                    tags__name__in=tag_list))).order_by('-common_tags')[:5]

    def __str__(self):
        return self.title


class Comment(models.Model):
    photo = models.ForeignKey(Photo,
                              on_delete=models.CASCADE,
                              related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Comment by {self.user.username} on {self.photo.title}'
