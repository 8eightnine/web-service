from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from photos import views as photos_views


def login_page(request):
    return render(request, 'login.html')


def register_page(request):
    return render(request, 'register.html')


def home_page(request):
    return photos_views.photo_list(request)


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Неверные учетные данные'})
    return render(request, 'login.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(username=username,
                                              email=email,
                                              password=password1)
                login(request, user)
                return redirect('home')
            else:
                return render(request, 'register.html', 
                            {'error': 'Пользователь с таким именем уже существует'})
        else:
            return render(request, 'register.html', 
                        {'error': 'Пароли не совпадают'})
    return render(request, 'register.html')

def logout_view(request):
    logout(request)
    return redirect('home')
