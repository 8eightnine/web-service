from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.views.generic import TemplateView
from django.views import View
from photos.views import PhotoListView


class HomePageView(PhotoListView):
    """Main home page - redirects to photo list"""
    def get(self, request):
        return redirect(PhotoListView.as_view())


class LoginView(View):
    """Handle user login"""
    template_name = 'login.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, self.template_name,
                          {'error': 'Неверные учетные данные'})


class RegisterView(View):
    """Handle user registration"""
    template_name = 'register.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
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
                return render(
                    request, self.template_name,
                    {'error': 'Пользователь с таким именем уже существует'})
        else:
            return render(request, self.template_name,
                          {'error': 'Пароли не совпадают'})


class LogoutView(View):
    """Handle user logout"""

    def get(self, request):
        logout(request)
        return redirect('home')

    def post(self, request):
        logout(request)
        return redirect('home')


# Keep old function-based views for backward compatibility
def login_page(request):
    return render(request, 'login.html')


def register_page(request):
    return render(request, 'register.html')


def home_page(request):
    from photos import views as photos_views
    return photos_views.PhotoListView.as_view()


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html',
                          {'error': 'Неверные учетные данные'})
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
                return render(
                    request, 'register.html',
                    {'error': 'Пользователь с таким именем уже существует'})
        else:
            return render(request, 'register.html',
                          {'error': 'Пароли не совпадают'})
    return render(request, 'register.html')


def logout_view(request):
    logout(request)
    return redirect('home')
