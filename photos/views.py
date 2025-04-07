from django.db.models import DateTimeField
from django.db.models.functions import ExtractYear
from django.shortcuts import render, get_object_or_404, redirect, Http404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import Photo, Category, PhotoCategory
from .forms import PhotoForm, CategoryForm


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


def redirect_to_home(request):
    return redirect('photo_list')


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
    return render(request, 'photos/home.html', {'recent_photos': recent_photos})
