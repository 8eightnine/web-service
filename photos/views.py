from django.db.models.functions import ExtractYear
from django.shortcuts import render, get_object_or_404, redirect, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.files.storage import default_storage
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.urls import reverse_lazy
from .models import Photo, Category, PhotoCategory
from .forms import CommentForm, PhotoForm, PhotoUploadForm
from .utils import DataMixin
from django.db.models import Count, Avg, Max, Value, FloatField, ExpressionWrapper, IntegerField, F
from datetime import date


class RedirectToHomeView(View):
    """Redirect to photo list page"""

    def get(self, request, *args, **kwargs):
        return redirect('photo_list')


class SimplePhotoView(View):
    """Simple View class for basic photo operations"""
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests - show simple photo info"""
        photos_count = Photo.objects.count()
        latest_photo = Photo.objects.order_by('-uploaded_at').first()
        
        context = {
            'photos_count': photos_count,
            'latest_photo': latest_photo,
            'message': 'Простой View для работы с фотографиями'
        }
        
        return render(request, 'photos/simple_view.html', context)
    
    def post(self, request, *args, **kwargs):
        """Handle POST requests - could be used for simple operations"""
        # Простая обработка POST запроса
        action = request.POST.get('action', '')
        
        if action == 'refresh_stats':
            messages.success(request, 'Статистика обновлена!')
        elif action == 'clear_cache':
            messages.info(request, 'Кэш очищен!')
        else:
            messages.warning(request, 'Неизвестное действие!')
            
        return self.get(request, *args, **kwargs)


class UploadPhotoView(DataMixin, CreateView):
    """Upload photo using ModelForm"""
    model = Photo
    form_class = PhotoForm
    template_name = 'photos/upload_photo.html'
    success_url = reverse_lazy('photo_list')
    title_page = 'Загрузить фотографию'

    def __init__(self):
        super().__init__()
        self.extra_context.update({
            'form_type':
            'ModelForm',
            'form_description':
            'Форма связанная с моделью (использует upload_to)'
        })

    def form_valid(self, form):
        try:
            photo = form.save(commit=False)
            if self.request.user.is_authenticated:
                photo.uploaded_by = self.request.user
            photo.save()

            # Handle tags
            tags_text = form.cleaned_data.get('tags', '')
            if tags_text:
                tags_list = [
                    tag.strip() for tag in tags_text.split(',') if tag.strip()
                ]
                photo.tags.add(*tags_list)

            self.success_url = reverse_lazy('photo_detail_slug',
                                            kwargs={'slug': photo.slug})
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f'Ошибка при загрузке: {str(e)}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        return super().form_invalid(form)


class UploadPhotoNonModelView(DataMixin, FormView):
    """Upload photo using regular Form (not ModelForm)"""
    form_class = PhotoUploadForm
    template_name = 'photos/upload_photo_non_model.html'
    success_url = reverse_lazy('photo_list')
    title_page = 'Загрузить фотографию (обычная форма)'

    def __init__(self):
        super().__init__()
        self.extra_context.update({
            'form_type':
            'Form',
            'form_description':
            'Форма НЕ связанная с моделью (также использует upload_to)'
        })

    def form_valid(self, form):
        try:
            # Create Photo object manually from form data
            photo = Photo(title=form.cleaned_data['title'],
                          description=form.cleaned_data['description'],
                          image=form.cleaned_data['image'],
                          category_type=form.cleaned_data['category_type'])

            if self.request.user.is_authenticated:
                photo.uploaded_by = self.request.user

            photo.save()

            # Handle tags
            tags_text = form.cleaned_data.get('tags', '')
            if tags_text:
                tags_list = [
                    tag.strip() for tag in tags_text.split(',') if tag.strip()
                ]
                photo.tags.add(*tags_list)

            self.success_url = reverse_lazy('photo_detail_slug',
                                            kwargs={'slug': photo.slug})
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f'Ошибка при загрузке: {str(e)}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        return super().form_invalid(form)


class EditPhotoView(DataMixin, LoginRequiredMixin, UpdateView):
    """Edit existing photo using UpdateView"""
    model = Photo
    form_class = PhotoForm
    template_name = 'photos/edit_photo.html'
    slug_url_kwarg = 'slug'
    title_page = 'Редактировать фотографию'

    def get_success_url(self):
        return reverse_lazy('photo_detail_slug',
                            kwargs={'slug': self.object.slug})

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.uploaded_by != self.request.user and not self.request.user.is_staff:
            messages.error(
                self.request,
                'У вас нет прав для редактирования этой фотографии.')
            raise Http404("Нет прав для редактирования")
        return obj

    def get_initial(self):
        """Set initial form data with existing tags"""
        initial = super().get_initial()
        initial['tags'] = ', '.join(
            [tag.name for tag in self.object.tags.all()])
        return initial

    def form_valid(self, form):
        try:
            updated_photo = form.save()

            # Handle tags
            tags_text = form.cleaned_data.get('tags', '')
            updated_photo.tags.clear()
            if tags_text:
                tags_list = [
                    tag.strip() for tag in tags_text.split(',') if tag.strip()
                ]
                updated_photo.tags.add(*tags_list)

            messages.success(self.request, 'Фотография успешно обновлена!')
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f'Ошибка при обновлении: {str(e)}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Пожалуйста, исправьте ошибки в форме.')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        """Add photo object to context for template"""
        context = super().get_context_data(**kwargs)
        context['photo'] = self.object
        return context


class DeletePhotoView(DataMixin, DeleteView):
    """Delete photo with confirmation"""
    model = Photo
    template_name = 'photos/delete_photo.html'
    slug_url_kwarg = 'slug'
    success_url = reverse_lazy('photo_list')
    title_page = 'Удалить фотографию'

    def get_object(self, queryset=None):
        """Get photo object without user permission checks"""
        obj = super().get_object(queryset)
        if obj.uploaded_by != self.request.user and not self.request.user.is_staff:
            messages.error(self.request,
                           'У вас нет прав для удаления этой фотографии.')
            raise Http404("Нет прав для удаления")
        return obj

    def delete(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            # Delete file from storage
            if self.object.image:
                default_storage.delete(self.object.image.name)

            success_url = self.get_success_url()
            self.object.delete()
            messages.success(request, 'Фотография успешно удалена!')
            return redirect(success_url)
        except Exception as e:
            messages.error(request, f'Ошибка при удалении: {str(e)}')
            return redirect('photo_detail_slug', slug=self.object.slug)


class PhotosByYearView(DataMixin, ListView):
    """Display photos filtered by year"""
    model = Photo
    template_name = 'photos/photos_by_year.html'
    context_object_name = 'photos'

    def get_queryset(self):
        year = self.kwargs['year']
        return Photo.objects.filter(uploaded_at__year=year)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.kwargs['year']
        years = Photo.objects.dates('uploaded_at',
                                    'year').values_list('uploaded_at__year',
                                                        flat=True)
        return self.get_mixin_context(context,
                                      year=year,
                                      years=years,
                                      title=f'Фотографии за {year} год')


class PhotosByCategoryView(DataMixin, ListView):
    """Display photos filtered by category"""
    model = Photo
    template_name = 'photos/photos_by_category.html'
    context_object_name = 'photos'

    def get_queryset(self):
        category_slug = self.kwargs['category_slug']
        return Photo.objects.filter(category_type=category_slug.upper())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_slug = self.kwargs['category_slug']
        return self.get_mixin_context(
            context,
            category_type=category_slug,
            title=f'Фотографии категории: {category_slug}')


class HomeView(DataMixin, TemplateView):
    """Home page with recent photos"""
    template_name = 'photos/home.html'
    title_page = 'Главная страница'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recent_photos = Photo.custom.get_recent(5)
        return self.get_mixin_context(context, recent_photos=recent_photos)


class PhotoListView(DataMixin, ListView):
    """List all photos with filtering and pagination"""
    model = Photo
    template_name = 'photos/photo_list.html'
    context_object_name = 'photos'
    title_page = 'Все фотографии'

    def get_queryset(self):
        sort_by = self.request.GET.get('sort', '-uploaded_at')
        category_filter = self.request.GET.get('category_type', None)
        tag_filter = self.request.GET.get('tag', None)

        photos = Photo.objects.all()

        if category_filter:
            photos = photos.filter(category_type=category_filter)

        if tag_filter:
            photos = photos.filter(tags__name=tag_filter)

        return photos.order_by(sort_by)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем параметры фильтрации
        category_filter = self.request.GET.get('category_type', None)
        tag_filter = self.request.GET.get('tag', None)
        sort_by = self.request.GET.get('sort', '-uploaded_at')

        # Получаем данные для фильтров
        years = Photo.objects.dates('uploaded_at',
                                    'year').values_list('uploaded_at__year',
                                                        flat=True)

        # ИСПРАВЛЕНИЕ: используем PhotoCategory.choices() вместо Category.objects.all()
        categories = PhotoCategory.choices(
        )  # Это возвращает список кортежей (type, name)

        popular_tags = Photo.tags.most_common()[:10]

        # Статистика
        category_counts = []
        for category_type, category_name in PhotoCategory.choices():
            count = Photo.objects.filter(category_type=category_type).count()
            category_counts.append(count)

        avg_photos_per_category = sum(category_counts) / len(
            category_counts) if category_counts else 0

        stats = {
            'total_photos':
            Photo.objects.count(),
            'avg_photos_per_category':
            avg_photos_per_category,
            'latest_photo':
            Photo.objects.latest('uploaded_at')
            if Photo.objects.exists() else None,
            'earliest_photo':
            Photo.objects.earliest('uploaded_at')
            if Photo.objects.exists() else None,
        }

        return self.get_mixin_context(
            context,
            years=years,
            categories=categories,  # Теперь это список кортежей
            popular_tags=popular_tags,
            current_category=category_filter,
            current_tag=tag_filter,
            current_sort=sort_by,
            stats=stats)


class PhotoDetailView(DataMixin, DetailView):
    """Display single photo with comments"""
    model = Photo
    template_name = 'photos/photo_detail.html'
    context_object_name = 'photo'
    slug_url_kwarg = 'slug'

    def get_object(self, queryset=None):
        pk = self.kwargs.get('pk')
        slug = self.kwargs.get('slug')

        if pk:
            try:
                return Photo.objects.get(pk=pk)
            except Photo.DoesNotExist:
                raise Http404("Фотография не найдена")
        elif slug:
            try:
                return Photo.objects.get(slug=slug)
            except Photo.DoesNotExist:
                raise Http404("Фотография не найдена")
        else:
            raise Http404("Неверный запрос")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        photo = self.object

        prev_photo = photo.get_previous_photo()
        next_photo = photo.get_next_photo()
        related_photos = photo.get_related_photos()
        comments = photo.comments.all()
        comment_form = CommentForm()

        return self.get_mixin_context(context,
                                      prev_photo=prev_photo,
                                      next_photo=next_photo,
                                      related_photos=related_photos,
                                      comments=comments,
                                      comment_form=comment_form,
                                      title=photo.title)

    def post(self, request, *args, **kwargs):
        """Handle comment submission - disabled since user system is not used"""
        # Убираем функциональность комментариев, так как система пользователей не используется
        messages.warning(request, 'Комментарии временно недоступны.')
        return redirect('photo_detail_slug', slug=self.kwargs.get('slug'))


class PhotosByTagView(DataMixin, ListView):
    """Display photos filtered by tag"""
    model = Photo
    template_name = 'photos/photos_by_tag.html'
    context_object_name = 'photos'

    def get_queryset(self):
        tag_slug = self.kwargs['tag_slug']
        from taggit.models import Tag

        try:
            # Try to find by exact slug
            tag = Tag.objects.get(slug=tag_slug)
            return Photo.objects.filter(tags__slug=tag_slug).distinct()
        except Tag.DoesNotExist:
            try:
                # Try to find by name (for Cyrillic tags)
                possible_name = tag_slug.replace('-', ' ')
                tag = Tag.objects.get(name__iexact=possible_name)
                return Photo.objects.filter(
                    tags__name__iexact=possible_name).distinct()
            except Tag.DoesNotExist:
                return Photo.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tag_slug = self.kwargs['tag_slug']

        from taggit.models import Tag
        try:
            tag = Tag.objects.get(slug=tag_slug)
            tag_name = tag.name
        except Tag.DoesNotExist:
            try:
                possible_name = tag_slug.replace('-', ' ')
                tag = Tag.objects.get(name__iexact=possible_name)
                tag_name = tag.name
            except Tag.DoesNotExist:
                tag_name = tag_slug.replace('-', ' ')

        return self.get_mixin_context(context,
                                      tag={
                                          'name': tag_name,
                                          'slug': tag_slug
                                      },
                                      title=f'Фотографии с тегом: {tag_name}')


class TagListView(DataMixin, ListView):
    """Display all tags with statistics"""
    template_name = 'photos/tag_list.html'
    context_object_name = 'tags'
    title_page = 'Все теги'

    def get_queryset(self):
        from taggit.models import Tag
        from django.db.models import Count
        return Tag.objects.annotate(photo_count=Count(
            'taggit_taggeditem_items')).order_by('-photo_count')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tags = self.get_queryset()

        stats = {
            'total_tags':
            tags.count(),
            'max_photos':
            tags.aggregate(Max('photo_count'))['photo_count__max']
            if tags.exists() else 0,
            'avg_photos':
            tags.aggregate(Avg('photo_count'))['photo_count__avg']
            if tags.exists() else 0,
        }

        return self.get_mixin_context(context, stats=stats)


class StatsView(DataMixin, TemplateView):
    """Display comprehensive statistics"""
    template_name = 'photos/stats.html'
    title_page = 'Статистика'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        total_photos = Photo.objects.count()

        categories_with_counts = []
        categories_with_percentages = []

        for category_type, category_name in PhotoCategory.choices():
            count = Photo.objects.filter(category_type=category_type).count()
            categories_with_counts.append({
                'name': category_name,
                'photo_count': count
            })

            if total_photos > 0:
                percentage = (count * 100.0) / total_photos
            else:
                percentage = 0

            categories_with_percentages.append({
                'name': category_name,
                'photo_count': count,
                'percentage': percentage
            })

        photos_per_year = Photo.objects.annotate(
            year=ExtractYear('uploaded_at')).values('year').annotate(
                count=Count('id'),
                percentage=ExpressionWrapper(
                    Count('id') * Value(100.0) /
                    Value(total_photos) if total_photos > 0 else Value(0.0),
                    output_field=FloatField())).order_by('year')

        photos_with_age = Photo.objects.annotate(
            age=ExpressionWrapper(Value(date.today().year) -
                                  ExtractYear('uploaded_at'),
                                  output_field=IntegerField()))

        latest_photo = Photo.objects.latest(
            'uploaded_at') if Photo.objects.exists() else None
        earliest_photo = Photo.objects.earliest(
            'uploaded_at') if Photo.objects.exists() else None
        first_photo = Photo.objects.order_by('id').first()
        last_photo = Photo.objects.order_by('id').last()

        return self.get_mixin_context(
            context,
            total_photos=total_photos,
            categories_with_counts=categories_with_counts,
            categories_with_percentages=categories_with_percentages,
            photos_per_year=photos_per_year,
            photos_with_age=photos_with_age,
            latest_photo=latest_photo,
            earliest_photo=earliest_photo,
            first_photo=first_photo,
            last_photo=last_photo)


# Keep the old function-based views for backward compatibility if needed
def redirect_to_home(request):
    return redirect('photo_list')


def upload_photo(request):
    """Загрузка фотографии с использованием формы, связанной с моделью"""
    if request.method == 'POST':
        form = PhotoForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                photo = form.save(commit=False)
                if request.user.is_authenticated:
                    photo.uploaded_by = request.user

                # Сохраняем фото - upload_to автоматически вызовется
                photo.save()

                # Обработка тегов
                tags_text = form.cleaned_data.get('tags', '')
                if tags_text:
                    tags_list = [
                        tag.strip() for tag in tags_text.split(',')
                        if tag.strip()
                    ]
                    photo.tags.add(*tags_list)

                return redirect('photo_detail_slug', slug=photo.slug)
            except Exception as e:
                messages.error(request, f'Ошибка при загрузке: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = PhotoForm()

    return render(
        request, 'photos/upload_photo.html', {
            'form': form,
            'form_type': 'ModelForm',
            'form_description':
            'Форма связанная с моделью (использует upload_to)'
        })


def upload_photo_non_model(request):
    """Загрузка фотографии с использованием формы, НЕ связанной с моделью"""
    if request.method == 'POST':
        form = PhotoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Создаем объект Photo из данных формы вручную
                photo = Photo(
                    title=form.cleaned_data['title'],
                    description=form.cleaned_data['description'],
                    image=form.
                    cleaned_data['image'],  # upload_to сработает при save()
                    category_type=form.cleaned_data['category_type'])

                # Убираем привязку к пользователю
                if request.user.is_authenticated:
                    photo.uploaded_by = request.user

                # При сохранении автоматически вызовется upload_to
                photo.save()

                # Обработка тегов
                tags_text = form.cleaned_data.get('tags', '')
                if tags_text:
                    tags_list = [
                        tag.strip() for tag in tags_text.split(',')
                        if tag.strip()
                    ]
                    photo.tags.add(*tags_list)

                return redirect('photo_detail_slug', slug=photo.slug)
            except Exception as e:
                messages.error(request, f'Ошибка при загрузке: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = PhotoUploadForm()

    return render(
        request, 'photos/upload_photo_non_model.html', {
            'form':
            form,
            'form_type':
            'Form',
            'form_description':
            'Форма НЕ связанная с моделью (также использует upload_to)'
        })


def edit_photo(request, slug):
    """Function-based view для редактирования (оставлен для совместимости)"""
    photo = get_object_or_404(Photo, slug=slug)

    if photo.uploaded_by != request.user and not request.user.is_staff:
        messages.error(request,
                       'У вас нет прав для редактирования этой фотографии.')
        return redirect('photo_detail_slug', slug=slug)

    if request.method == 'POST':
        form = PhotoForm(request.POST, request.FILES, instance=photo)
        if form.is_valid():
            try:
                # При сохранении новое изображение будет обработано через upload_to
                updated_photo = form.save()

                # Обработка тегов
                tags_text = form.cleaned_data.get('tags', '')
                updated_photo.tags.clear()
                if tags_text:
                    tags_list = [
                        tag.strip() for tag in tags_text.split(',')
                        if tag.strip()
                    ]
                    updated_photo.tags.add(*tags_list)

                messages.success(request, 'Фотография успешно обновлена!')
                return redirect('photo_detail_slug', slug=updated_photo.slug)
            except Exception as e:
                messages.error(request, f'Ошибка при обновлении: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        initial_data = {
            'tags': ', '.join([tag.name for tag in photo.tags.all()])
        }
        form = PhotoForm(instance=photo, initial=initial_data)

    return render(request, 'photos/edit_photo.html', {
        'form': form,
        'photo': photo
    })


def delete_photo(request, slug):
    """Function-based view для удаления (оставлен для совместимости)"""
    photo = get_object_or_404(Photo, slug=slug)

    # Убираем проверку прав пользователя
    # if photo.uploaded_by != request.user and not request.user.is_staff:
    #     messages.error(request, 'У вас нет прав для удаления этой фотографии.')
    #     return redirect('photo_detail_slug', slug=slug)

    if request.method == 'POST':
        try:
            # Удаляем файл из хранилища
            if photo.image:
                default_storage.delete(photo.image.name)
            photo.delete()
            messages.success(request, 'Фотография успешно удалена!')
            return redirect('photo_list')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении: {str(e)}')

    return render(request, 'photos/delete_photo.html', {'photo': photo})


# Остальные function-based views остаются без изменений...
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


def photos_by_category(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    photos = Photo.objects.filter(category_type=category_slug.upper())

    return render(request, 'photos/photos_by_category.html', {
        'photos': photos,
        'category_type': category_slug
    })


def home(request):
    recent_photos = Photo.custom.get_recent(5)
    return render(request, 'photos/home.html',
                  {'recent_photos': recent_photos})


def photo_list(request):
    sort_by = request.GET.get('sort', '-uploaded_at')
    category_filter = request.GET.get('category_type', None)
    tag_filter = request.GET.get('tag', None)

    photos = Photo.objects.all()

    if category_filter:
        photos = photos.filter(category_type=category_filter)

    if tag_filter:
        photos = photos.filter(tags__name=tag_filter)

    photos = photos.order_by(sort_by)

    years = Photo.objects.dates('uploaded_at',
                                'year').values_list('uploaded_at__year',
                                                    flat=True)
    categories = Category.objects.all()
    popular_tags = Photo.tags.most_common()[:10]

    category_counts = []
    for category_type, category_name in PhotoCategory.choices():
        count = Photo.objects.filter(category_type=category_type).count()
        category_counts.append(count)

    avg_photos_per_category = sum(category_counts) / len(
        category_counts) if category_counts else 0

    stats = {
        'total_photos':
        Photo.objects.count(),
        'avg_photos_per_category':
        avg_photos_per_category,
        'latest_photo':
        Photo.objects.latest('uploaded_at')
        if Photo.objects.exists() else None,
        'earliest_photo':
        Photo.objects.earliest('uploaded_at')
        if Photo.objects.exists() else None,
    }

    return render(
        request, 'photos/photo_list.html', {
            'photos': photos,
            'years': years,
            'categories': categories,
            'popular_tags': popular_tags,
            'current_category': category_filter,
            'current_tag': tag_filter,
            'current_sort': sort_by,
            'stats': stats
        })


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

    prev_photo = photo.get_previous_photo()
    next_photo = photo.get_next_photo()
    related_photos = photo.get_related_photos()

    # Убираем функциональность комментариев
    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            try:
                comment = comment_form.save(commit=False)
                comment.photo = photo
                comment.user = request.user
                comment.save()
                messages.success(request, 'Комментарий добавлен!')
                return redirect('photo_detail_slug', slug=photo.slug)
            except Exception as e:
                messages.error(request,
                               f'Ошибка при добавлении комментария: {str(e)}')
        else:
            messages.error(request,
                           'Пожалуйста, исправьте ошибки в комментарии.')
    else:
        comment_form = CommentForm()

    comments = photo.comments.all()

    return render(
        request, 'photos/photo_detail.html', {
            'photo': photo,
            'prev_photo': prev_photo,
            'next_photo': next_photo,
            'related_photos': related_photos,
            'comments': comments,
            'comment_form': comment_form
        })


def photos_by_tag(request, tag_slug):
    """Фотографии по тегу с поддержкой кириллицы"""
    from taggit.models import Tag
    from django.utils.text import slugify

    try:
        # Сначала пробуем найти по точному slug
        tag = Tag.objects.get(slug=tag_slug)
        photos = Photo.objects.filter(tags__slug=tag_slug).distinct()
        tag_name = tag.name
    except Tag.DoesNotExist:
        try:
            # Если не найден, пробуем найти по имени (для кириллических тегов)
            # Преобразуем slug обратно в возможное имя
            possible_name = tag_slug.replace('-', ' ')
            tag = Tag.objects.get(name__iexact=possible_name)
            photos = Photo.objects.filter(
                tags__name__iexact=possible_name).distinct()
            tag_name = tag.name
        except Tag.DoesNotExist:
            # Если тег не найден вообще
            photos = Photo.objects.none()
            tag_name = tag_slug.replace('-', ' ')

    return render(request, 'photos/photos_by_tag.html', {
        'photos': photos,
        'tag': {
            'name': tag_name,
            'slug': tag_slug
        }
    })


def tag_list(request):
    from taggit.models import Tag
    from django.db.models import Count

    tags = Tag.objects.annotate(
        photo_count=Count('taggit_taggeditem_items')).order_by('-photo_count')

    stats = {
        'total_tags':
        tags.count(),
        'max_photos':
        tags.aggregate(Max('photo_count'))['photo_count__max']
        if tags.exists() else 0,
        'avg_photos':
        tags.aggregate(Avg('photo_count'))['photo_count__avg']
        if tags.exists() else 0,
    }

    return render(request, 'photos/tag_list.html', {
        'tags': tags,
        'stats': stats
    })


def stats_view(request):
    total_photos = Photo.objects.count()

    categories_with_counts = []
    categories_with_percentages = []

    for category_type, category_name in PhotoCategory.choices():
        count = Photo.objects.filter(category_type=category_type).count()
        categories_with_counts.append({
            'name': category_name,
            'photo_count': count
        })

        if total_photos > 0:
            percentage = (count * 100.0) / total_photos
        else:
            percentage = 0

        categories_with_percentages.append({
            'name': category_name,
            'photo_count': count,
            'percentage': percentage
        })

    photos_per_year = Photo.objects.annotate(
        year=ExtractYear('uploaded_at')).values('year').annotate(
            count=Count('id'),
            percentage=ExpressionWrapper(
                Count('id') * Value(100.0) /
                Value(total_photos) if total_photos > 0 else Value(0.0),
                output_field=FloatField())).order_by('year')

    photos_with_age = Photo.objects.annotate(
        age=ExpressionWrapper(Value(date.today().year) -
                              ExtractYear('uploaded_at'),
                              output_field=IntegerField()))

    latest_photo = Photo.objects.latest(
        'uploaded_at') if Photo.objects.exists() else None
    earliest_photo = Photo.objects.earliest(
        'uploaded_at') if Photo.objects.exists() else None

    first_photo = Photo.objects.order_by('id').first()
    last_photo = Photo.objects.order_by('id').last()

    return render(
        request, 'photos/stats.html', {
            'total_photos': total_photos,
            'categories_with_counts': categories_with_counts,
            'categories_with_percentages': categories_with_percentages,
            'photos_per_year': photos_per_year,
            'photos_with_age': photos_with_age,
            'latest_photo': latest_photo,
            'earliest_photo': earliest_photo,
            'first_photo': first_photo,
            'last_photo': last_photo,
        })
