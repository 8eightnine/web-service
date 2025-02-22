from django.db.models import DateTimeField
from django.db.models.functions import ExtractYear
from django.shortcuts import render, get_object_or_404, redirect, Http404
from .models import Photo
from .forms import PhotoForm

def photo_list(request):
    photos = Photo.objects.all()
    # Получаем список уникальных годов
    years = Photo.objects.dates('uploaded_at', 'year').values_list('uploaded_at__year', flat=True)
    return render(request, 'photos/photo_list.html', {
        'photos': photos,
        'years': years
    })

def redirect_to_home(request):
    return redirect('photo_list')

def photo_detail(request, pk):
    try:
        photo = Photo.objects.get(pk=pk)
    except Photo.DoesNotExist:
        raise Http404("Фотография не найдена")
    return render(request, 'photos/photo_detail.html', {'photo': photo})

def upload_photo(request):
    if request.method == 'POST':
        form = PhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            if request.user.is_authenticated:  # Привязываем фотографию к пользователю, если он аутентифицирован
                photo.uploaded_by = request.user
            photo.save()
            return redirect('photo_list')
    else:
        form = PhotoForm()
    return render(request, 'photos/upload_photo.html', {'form': form})

def photos_by_year(request, year):
    photos = Photo.objects.filter(uploaded_at__year=year)
    years = Photo.objects.dates('uploaded_at', 'year').values_list('uploaded_at__year', flat=True)
    return render(request, 'photos/photos_by_year.html', {
        'photos': photos,
        'year': year,
        'years': years
    })


def home(request):
    return render(request, 'photos/home.html')
