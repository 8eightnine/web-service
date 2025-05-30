from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from .models import Photo, Category, Comment
from django.contrib.admin import SimpleListFilter

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 1
    readonly_fields = ('created_at',)

class HasTagsFilter(SimpleListFilter):
    title = 'Наличие тегов'
    parameter_name = 'has_tags'
    
    def lookups(self, request, model_admin):
        return (
            ('yes', 'Есть теги'),
            ('no', 'Нет тегов'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(tags__isnull=False).distinct()
        if self.value() == 'no':
            return queryset.filter(tags__isnull=True)

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('title', 'display_image', 'category_type', 'uploaded_by', 'uploaded_at', 'tag_list')
    list_filter = ('category_type', 'uploaded_at', HasTagsFilter)
    search_fields = ('title', 'description', 'tags__name')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('uploaded_at', 'display_large_image')
    inlines = [CommentInline]
    actions = ['mark_as_nature', 'mark_as_architecture', 'download_photos']
    date_hierarchy = 'uploaded_at'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'description', 'image', 'display_large_image')
        }),
        ('Категоризация', {
            'fields': ('category_type', 'tags'),
            'classes': ('collapse',),
        }),
        ('Метаданные', {
            'fields': ('uploaded_by', 'uploaded_at'),
            'classes': ('collapse',),
        }),
    )
    
    # Пользовательское поле 1: отображение миниатюры
    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return "Нет изображения"
    display_image.short_description = 'Миниатюра'
    
    # Пользовательское поле 2: отображение большого изображения
    def display_large_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="300" style="max-height: 300px; object-fit: contain;" />', obj.image.url)
        return "Нет изображения"
    display_large_image.short_description = 'Предпросмотр'
    
    # Пользовательское поле 3: список тегов
    def tag_list(self, obj):
        return ", ".join(o.name for o in obj.tags.all())
    tag_list.short_description = 'Теги'
    
    # Пользовательское действие 1
    def mark_as_nature(self, request, queryset):
        updated = queryset.update(category_type='NATURE')
        self.message_user(
            request, 
            f'Обновлено {updated} фотографий - установлена категория "Природа"',
            messages.SUCCESS
        )
    mark_as_nature.short_description = "Отметить как 'Природа'"
    
    # Пользовательское действие 2
    def mark_as_architecture(self, request, queryset):
        updated = queryset.update(category_type='ARCHITECTURE')
        self.message_user(
            request, 
            f'Обновлено {updated} фотографий - установлена категория "Архитектура"',
            messages.SUCCESS
        )
    mark_as_architecture.short_description = "Отметить как 'Архитектура'"
    
    # Пользовательское действие 3
    def download_photos(self, request, queryset):
        from django.http import HttpResponse
        import os
        
        if queryset.count() > 1:
            self.message_user(request, 'Можно скачать только одну фотографию за раз. Выберите одну фотографию.', messages.ERROR)
            return
        
        photo = queryset.first()
        if not photo.image:
            self.message_user(request, 'У выбранной фотографии нет изображения', messages.ERROR)
            return
        
        if not os.path.exists(photo.image.path):
            self.message_user(request, 'Файл изображения не найден на сервере', messages.ERROR)
            return
        
        try:
            with open(photo.image.path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/octet-stream')
                filename = os.path.basename(photo.image.name)
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                self.message_user(request, f'Фотография "{filename}" успешно скачана', messages.SUCCESS)
                return response
        except Exception as e:
            self.message_user(request, f'Ошибка при скачивании файла: {str(e)}', messages.ERROR)
            return
    download_photos.short_description = "Скачать выбранную фотографию"

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'photo', 'text_preview', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('text', 'user__username', 'photo__title')
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Комментарий'
