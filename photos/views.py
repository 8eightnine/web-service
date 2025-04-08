from itertools import count
from django.db.models import DateTimeField
from django.db.models.functions import ExtractYear
from django.shortcuts import render, get_object_or_404, redirect, Http404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils.text import slugify
from .models import Photo, Category, PhotoCategory, Tag
from .forms import CommentForm, PhotoForm, CategoryForm
from django.db.models import Count, Sum, Avg, Max, Min


def redirect_to_home(request):
    return redirect('photo_list')


def upload_photo(request):
    if request.method == 'POST':
        form = PhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            if request.user.is_authenticated:
                photo.uploaded_by = request.user
            photo.save()
            # Change this line to use the correct URL name for slug-based detail view
            return redirect('photo_detail_slug', slug=photo.slug)
    else:
        form = PhotoForm()
    return render(request, 'photos/upload_photo.html', {'form': form})


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
    photos = Photo.objects.filter(category=category)

    return render(request, 'photos/photos_by_category.html', {
        'photos': photos,
        'category': category
    })


def home(request):
    # Using custom manager to get recent photos
    recent_photos = Photo.custom.get_recent(5)
    return render(request, 'photos/home.html',
                  {'recent_photos': recent_photos})


def photo_list(request):
    sort_by = request.GET.get('sort', '-uploaded_at')
    category_filter = request.GET.get('category', None)
    tag_filter = request.GET.get('tag', None)

    photos = Photo.objects.all()

    # Apply filtering
    if category_filter:
        photos = photos.filter(category__slug=category_filter)

    if tag_filter:
        photos = photos.filter(tags__slug=tag_filter)

    # Apply sorting
    photos = photos.order_by(sort_by)

    # Get unique years
    years = Photo.objects.dates('uploaded_at',
                                'year').values_list('uploaded_at__year',
                                                    flat=True)

    # Get all categories for filter
    categories = Category.objects.all()

    # Get popular tags
    popular_tags = Tag.objects.annotate(
        photo_count=Count('photos')).order_by('-photo_count')[:10]

    # Get stats
    stats = {
        'total_photos':
        Photo.objects.count(),
        'avg_photos_per_category':
        Category.objects.annotate(photo_count=Count('photos')).aggregate(
            avg=Avg('photo_count'))['avg'],
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

    return render(
        request, 'photos/photo_detail.html', {
            'photo': photo,
            'prev_photo': prev_photo,
            'next_photo': next_photo,
            'related_photos': related_photos,
            'comments': comments,
            'comment_form': comment_form
        })


def upload_photo(request):
    if request.method == 'POST':
        form = PhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            if request.user.is_authenticated:
                photo.uploaded_by = request.user
            photo.save()

            # Handle tags
            tags = form.cleaned_data.get('tags')
            if tags:
                for tag_name in tags.split(','):
                    tag_name = tag_name.strip()
                    if tag_name:
                        tag, created = Tag.objects.get_or_create(
                            name=tag_name,
                            defaults={'slug': slugify(tag_name)})
                        photo.tags.add(tag)

            return redirect('photo_detail_slug', slug=photo.slug)
    else:
        form = PhotoForm()
    return render(request, 'photos/upload_photo.html', {'form': form})


def photos_by_tag(request, tag_slug):
    tag = get_object_or_404(Tag, slug=tag_slug)
    photos = Photo.objects.filter(tags=tag)

    return render(request, 'photos/photos_by_tag.html', {
        'photos': photos,
        'tag': tag
    })


def tag_list(request):
    # Use aggregation to get tags with photo counts
    tags = Tag.objects.annotate(
        photo_count=Count('photos')).order_by('-photo_count')

    # Get stats using aggregation
    stats = {
        'total_tags': tags.count(),
        'max_photos': tags.aggregate(Max('photo_count'))['photo_count__max'],
        'avg_photos': tags.aggregate(Avg('photo_count'))['photo_count__avg'],
    }

    return render(request, 'photos/tag_list.html', {
        'tags': tags,
        'stats': stats
    })


def stats_view(request):
    # Use various database operations to generate statistics

    # Count total photos
    total_photos = Photo.objects.count()

    # Photos per category using Count and annotation
    categories_with_counts = Category.objects.annotate(
        photo_count=Count('photos')).order_by('-photo_count')

    # Photos per year using Extract and grouping
    photos_per_year = Photo.objects.annotate(
        year=ExtractYear('uploaded_at')).values('year').annotate(
            count=Count('id')).order_by('year')

    # Latest and earliest photos
    latest_photo = Photo.objects.latest(
        'uploaded_at') if Photo.objects.exists() else None
    earliest_photo = Photo.objects.earliest(
        'uploaded_at') if Photo.objects.exists() else None

    # First and last photos by ID
    first_photo = Photo.objects.order_by('id').first()
    last_photo = Photo.objects.order_by('id').last()

    return render(
        request, 'photos/stats.html', {
            'total_photos': total_photos,
            'categories_with_counts': categories_with_counts,
            'photos_per_year': photos_per_year,
            'latest_photo': latest_photo,
            'earliest_photo': earliest_photo,
            'first_photo': first_photo,
            'last_photo': last_photo,
        })
