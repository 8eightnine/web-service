from django.db.models.functions import ExtractYear
from django.shortcuts import render, get_object_or_404, redirect, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.files.storage import default_storage
from django.views import View
from django.views.generic import TemplateView, ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.urls import reverse_lazy
from .models import Photo, Category, PhotoCategory, Comment, PhotoLike
from .forms import CommentForm, PhotoForm, PhotoUploadForm
from .utils import DataMixin
from django.db.models import Count, Avg, Max, Value, FloatField, ExpressionWrapper, IntegerField, F
from datetime import date


class RedirectToHomeView(View):
    """Перенаправление на главную страницу"""

    def get(self, request, *args, **kwargs):
        return redirect('photos:photo_list')


class SimplePhotoView(View):
    """Простой View для работы с фотографиями"""
    
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
        """Реализация POST запроса"""
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
    """Загрузка фотографии"""
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
    """Загрузка фотографии с использованием обычной формы"""
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
            # Создание объекта Photo без сохранения в базу данных
            photo = Photo(title=form.cleaned_data['title'],
                          description=form.cleaned_data['description'],
                          image=form.cleaned_data['image'],
                          category_type=form.cleaned_data['category_type'])

            if self.request.user.is_authenticated:
                photo.uploaded_by = self.request.user

            photo.save()

            # Работа с тегами
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
    """Редактирование фотографии"""
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
        """Заполнение полей формы из объекта модели"""
        initial = super().get_initial()
        initial['tags'] = ', '.join(
            [tag.name for tag in self.object.tags.all()])
        return initial

    def form_valid(self, form):
        try:
            updated_photo = form.save()

            # Редактирование тегов
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
        """Добавляем объект фотографии в контекст"""
        context = super().get_context_data(**kwargs)
        context['photo'] = self.object
        return context


class DeletePhotoView(DataMixin, DeleteView):
    """Удаление фото"""
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
            # Удаляем файл с сервера
            if self.object.image:
                default_storage.delete(self.object.image.name)

            success_url = self.get_success_url()
            self.object.delete()
            messages.success(request, 'Фотография успешно удалена!')
            return redirect(success_url)
        except Exception as e:
            messages.error(request, f'Ошибка при удалении: {str(e)}')
            return redirect('photos:photo_detail_slug', slug=self.object.slug)


class PhotosByYearView(DataMixin, ListView):
    """Список фото по годам"""
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
    """Список фото по категориям"""
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
    """Домашная страница"""
    template_name = 'photos/home.html'
    title_page = 'Главная страница'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        recent_photos = Photo.custom.get_recent(5)
        return self.get_mixin_context(context, recent_photos=recent_photos)


class PhotoListView(DataMixin, ListView):
    """Список фотографий с пагинацией"""
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

        categories = PhotoCategory.choices()  # Это возвращает список кортежей (type, name)

        popular_tags = Photo.tags.most_common()[:10]

        # Статистика
        category_counts = []
        for category_type in PhotoCategory.choices():
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
            categories=categories,
            popular_tags=popular_tags,
            current_category=category_filter,
            current_tag=tag_filter,
            current_sort=sort_by,
            stats=stats)


class PhotoDetailView(DataMixin, DetailView):
    """Подробная карточка фотографии с комментариями"""
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
        
        # Получаем комментарии (только родительские, без ответов)
        comments = photo.comments.filter(parent=None).select_related('user').order_by('-created_at')
        
        # Формы для комментариев
        comment_form = CommentForm()
        
        # Проверяем реакцию пользователя на фото (если есть система лайков)
        user_reaction = None
        if self.request.user.is_authenticated and hasattr(photo, 'user_reaction'):
            user_reaction = photo.user_reaction(self.request.user)

        return self.get_mixin_context(context,
                                      prev_photo=prev_photo,
                                      next_photo=next_photo,
                                      related_photos=related_photos,
                                      comments=comments,
                                      comment_form=comment_form,
                                      user_reaction=user_reaction,
                                      title=photo.title)

    def post(self, request, *args, **kwargs):
        """Комментирование фото"""
        self.object = self.get_object()
        photo = self.object
        
        # Обработка лайков/дизлайков
        if 'like_action' in request.POST:
            if not request.user.is_authenticated:
                messages.warning(request, 'Для оценки фотографий необходимо войти в систему.')
                return redirect('photos:photo_detail_slug', slug=photo.slug)
            
            action = request.POST.get('like_action')
            try:
                existing_like = PhotoLike.objects.get(user=request.user, photo=photo)
                if existing_like.value == int(action):
                    # Если пользователь нажал на ту же кнопку - убираем оценку
                    existing_like.delete()
                    messages.info(request, 'Оценка убрана.')
                else:
                    # Меняем оценку
                    existing_like.value = int(action)
                    existing_like.save()
                    action_text = 'лайк' if int(action) == 1 else 'дизлайк'
                    messages.success(request, f'Поставлен {action_text}!')
            except PhotoLike.DoesNotExist:
                # Создаем новую оценку
                PhotoLike.objects.create(user=request.user, photo=photo, value=int(action))
                action_text = 'лайк' if int(action) == 1 else 'дизлайк'
                messages.success(request, f'Поставлен {action_text}!')
            
            return redirect('photos:photo_detail_slug', slug=photo.slug)
        
        # Обработка комментариев (существующий код)
        if not request.user.is_authenticated:
            messages.warning(request, 'Для добавления комментариев необходимо войти в систему.')
            return redirect('photos:photo_detail_slug', slug=photo.slug)
        
        comment_form = CommentForm(request.POST)
        
        if comment_form.is_valid():
            try:
                comment = comment_form.save(commit=False)
                comment.photo = photo
                comment.user = request.user
                
                # Проверяем, есть ли parent_id для ответа на комментарий
                parent_id = request.POST.get('parent_id')
                if parent_id:
                    try:
                        parent_comment = Comment.objects.get(id=parent_id, photo=photo)
                        Comment.parent = parent_comment
                    except comment.DoesNotExist:
                        pass
                
                comment.save()
                messages.success(request, 'Комментарий успешно добавлен!')
                
            except Exception as e:
                messages.error(request, f'Ошибка при добавлении комментария: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в комментарии.')
        
        return redirect('photos:photo_detail_slug', slug=photo.slug)


class PhotosByTagView(DataMixin, ListView):
    """Отображение фотографий по тегу"""
    model = Photo
    template_name = 'photos/photos_by_tag.html'
    context_object_name = 'photos'

    def get_queryset(self):
        tag_slug = self.kwargs['tag_slug']
        from taggit.models import Tag # type: ignore

        try:
            # Пытаемся найти тег по slug
            tag = Tag.objects.get(slug=tag_slug)
            return Photo.objects.filter(tags__slug=tag_slug).distinct()
        except Tag.DoesNotExist:
            try:
                # Пытаемся найти тег по возможному варианту (кириллица)
                possible_name = tag_slug.replace('-', ' ')
                tag = Tag.objects.get(name__iexact=possible_name)
                return Photo.objects.filter(
                    tags__name__iexact=possible_name).distinct()
            except Tag.DoesNotExist:
                return Photo.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tag_slug = self.kwargs['tag_slug']

        from taggit.models import Tag # type: ignore
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
    """Показать все теги"""
    template_name = 'photos/tag_list.html'
    context_object_name = 'tags'
    title_page = 'Все теги'

    def get_queryset(self):
        from taggit.models import Tag # type: ignore
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
    """Показать статистику"""
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


@login_required
def delete_comment(request, comment_id):
    """Удаление комментария"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Проверяем права на удаление
    if comment.user != request.user and not request.user.is_staff:
        messages.error(request, 'У вас нет прав для удаления этого комментария.')
        return redirect('photos:photo_detail_slug', slug=comment.photo.slug)
    
    photo_slug = comment.photo.slug
    comment.delete()
    messages.success(request, 'Комментарий удален!')
    
    return redirect('photos:photo_detail_slug', slug=photo_slug)

@login_required 
def edit_comment(request, comment_id):
    """Редактирование комментария"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # Проверяем права на редактирование
    if comment.user != request.user and not request.user.is_staff:
        messages.error(request, 'У вас нет прав для редактирования этого комментария.')
        return redirect('photos:photo_detail_slug', slug=comment.photo.slug)
    
    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Комментарий обновлен!')
            return redirect('photos:photo_detail_slug', slug=comment.photo.slug)
    else:
        form = CommentForm(instance=comment)
    
    context = {
        'form': form,
        'comment': comment,
        'title': 'Редактировать комментарий'
    }
    return render(request, 'photos/edit_comment.html', context)
