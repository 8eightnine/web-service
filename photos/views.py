from django.db.models.functions import ExtractYear
from django.shortcuts import render, get_object_or_404, redirect, Http404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Photo, Category, PhotoCategory
from .forms import CommentForm, PhotoForm, PhotoUploadForm
from django.db.models import Count, Avg, Max, Value, FloatField, ExpressionWrapper, IntegerField, F
from datetime import date


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
                photo.save()
                
                # Обработка тегов
                tags_text = form.cleaned_data.get('tags', '')
                if tags_text:
                    tags_list = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
                    photo.tags.add(*tags_list)
                
                messages.success(request, 'Фотография успешно загружена!')
                return redirect('photo_detail_slug', slug=photo.slug)
            except Exception as e:
                messages.error(request, f'Ошибка при загрузке: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = PhotoForm()
    
    return render(request, 'photos/upload_photo.html', {
        'form': form,
        'form_type': 'ModelForm',
        'form_description': 'Форма связанная с моделью'
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
                    image=form.cleaned_data['image'],
                    category_type=form.cleaned_data['category_type']
                )
                
                if request.user.is_authenticated:
                    photo.uploaded_by = request.user
                
                photo.save()
                
                # Обработка тегов
                tags_text = form.cleaned_data.get('tags', '')
                if tags_text:
                    tags_list = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
                    photo.tags.add(*tags_list)
                
                messages.success(request, 'Фотография успешно загружена!')
                return redirect('photo_detail_slug', slug=photo.slug)
            except Exception as e:
                messages.error(request, f'Ошибка при загрузке: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        form = PhotoUploadForm()
    
    return render(request, 'photos/upload_photo_non_model.html', {
        'form': form,
        'form_type': 'Form',
        'form_description': 'Форма НЕ связанная с моделью'
    })


@login_required
def edit_photo(request, slug):
    photo = get_object_or_404(Photo, slug=slug)

    if photo.uploaded_by != request.user and not request.user.is_staff:
        messages.error(request, 'У вас нет прав для редактирования этой фотографии.')
        return redirect('photo_detail_slug', slug=slug)

    if request.method == 'POST':
        form = PhotoForm(request.POST, request.FILES, instance=photo)
        if form.is_valid():
            try:
                form.save()
                
                # Обработка тегов
                tags_text = form.cleaned_data.get('tags', '')
                photo.tags.clear()
                if tags_text:
                    tags_list = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
                    photo.tags.add(*tags_list)
                
                messages.success(request, 'Фотография успешно обновлена!')
                return redirect('photo_detail_slug', slug=photo.slug)
            except Exception as e:
                messages.error(request, f'Ошибка при обновлении: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else:
        initial_data = {'tags': ', '.join([tag.name for tag in photo.tags.all()])}
        form = PhotoForm(instance=photo, initial=initial_data)

    return render(request, 'photos/edit_photo.html', {
        'form': form,
        'photo': photo
    })


@login_required
def delete_photo(request, slug):
    photo = get_object_or_404(Photo, slug=slug)

    if photo.uploaded_by != request.user and not request.user.is_staff:
        messages.error(request, 'У вас нет прав для удаления этой фотографии.')
        return redirect('photo_detail_slug', slug=slug)

    if request.method == 'POST':
        try:
            photo.delete()
            messages.success(request, 'Фотография успешно удалена!')
            return redirect('photo_list')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении: {str(e)}')

    return render(request, 'photos/delete_photo.html', {'photo': photo})


def photos_by_year(request, year):
    photos = Photo.objects.filter(uploaded_at__year=year)
    years = Photo.objects.dates('uploaded_at', 'year').values_list('uploaded_at__year', flat=True)
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
    return render(request, 'photos/home.html', {'recent_photos': recent_photos})


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

    years = Photo.objects.dates('uploaded_at', 'year').values_list('uploaded_at__year', flat=True)
    categories = Category.objects.all()
    popular_tags = Photo.tags.most_common()[:10]

    category_counts = []
    for category_type, category_name in PhotoCategory.choices():
        count = Photo.objects.filter(category_type=category_type).count()
        category_counts.append(count)
    
    avg_photos_per_category = sum(category_counts) / len(category_counts) if category_counts else 0

    stats = {
        'total_photos': Photo.objects.count(),
        'avg_photos_per_category': avg_photos_per_category,
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
                messages.error(request, f'Ошибка при добавлении комментария: {str(e)}')
        else:
            messages.error(request, 'Пожалуйста, исправьте ошибки в комментарии.')
    else:
        comment_form = CommentForm()

    comments = photo.comments.all()

    return render(request, 'photos/photo_detail.html', {
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
            photos = Photo.objects.filter(tags__name__iexact=possible_name).distinct()
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
        'total_tags': tags.count(),
        'max_photos': tags.aggregate(Max('photo_count'))['photo_count__max'] if tags.exists() else 0,
        'avg_photos': tags.aggregate(Avg('photo_count'))['photo_count__avg'] if tags.exists() else 0,
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
        year=ExtractYear('uploaded_at')
    ).values('year').annotate(
        count=Count('id'),
        percentage=ExpressionWrapper(
            Count('id') * Value(100.0) / Value(total_photos) if total_photos > 0 else Value(0.0),
            output_field=FloatField()
        )
    ).order_by('year')

    photos_with_age = Photo.objects.annotate(
        age=ExpressionWrapper(
            Value(date.today().year) - ExtractYear('uploaded_at'),
            output_field=IntegerField()
        )
    )

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
