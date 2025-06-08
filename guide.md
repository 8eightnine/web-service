Of course. Based on the theoretical information from the provided document, here is a detailed, self-contained instruction set for an AI to implement a comprehensive user authentication and management system in a generic Django project.

***

### **Instruction for AI: Implementing User Authentication and Management in Django**

Your task is to implement a complete user registration, authentication, profile management, and permissions system in a Django project. Follow these steps precisely, using the provided concepts and code structures.

**Objective:** Create a standalone application within the Django project to handle all user-related functionalities, including registration, login/logout, password reset via email, user profiles, and access control using permissions and groups.

---

#### **Part 1: Initial Application Setup**

1.  **Create a `users` Application:**
    In your project's root directory, execute the command to create a new application for handling users:
    ```bash
    python manage.py startapp users
    ```

2.  **Configure the Project:**
    * Open your project's `settings.py` file.
    * Add the new `users` app to the `INSTALLED_APPS` list. It's crucial to use the application's config class.
        ```python
        INSTALLED_APPS = [
            "users.apps.UsersConfig",
            # ... other apps
        ]
        ```
    * Verify that `django.contrib.sessions.middleware.SessionMiddleware` and `django.contrib.auth.middleware.AuthenticationMiddleware` are present in the `MIDDLEWARE` list, as they are essential for authentication.

3.  **Set Up URL Routing:**
    * Create a new file named `urls.py` inside your `users` application directory.
    * Add the following initial configuration to `users/urls.py` to define an application-specific namespace and routes for login and logout.
        ```python
        from django.urls import path
        from . import views

        app_name = "users"

        urlpatterns = [
            path('login/', views.LoginUser.as_view(), name='login'),
            path('logout/', views.logout_user, name='logout'),
        ]
        ```
    * In your main project's `urls.py` file, include the URLs from the `users` app and assign them a namespace. This prevents URL name conflicts between different apps.
        ```python
        from django.urls import path, include

        urlpatterns = [
            # ... other project urls
            path('users/', include('users.urls', namespace="users")),
        ]
        ```

---

#### **Part 2: Authentication (Login & Logout)**

1.  **Create the Login View:**
    * In `users/views.py`, use Django's built-in `LoginView` for a robust and secure login implementation.
    * It uses `AuthenticationForm` by default, which handles the authentication logic.
    * Override `get_success_url` to redirect users to the home page after a successful login.
        ```python
        from django.urls import reverse_lazy
        from django.contrib.auth.views import LoginView

        class LoginUser(LoginView):
            template_name = 'users/login.html'
            extra_context = {'title': 'Авторизация'}

            def get_success_url(self):
                return reverse_lazy('home')
        ```
    * Alternatively, you can define a global redirect URL in `settings.py`: `LOGIN_REDIRECT_URL = 'home'`.

2.  **Create the Login Template:**
    * Create the template file `users/templates/users/login.html`.
    * The template should contain a form. Use `{{ form.as_p }}` to render the form fields and `{% csrf_token %}` for security. To display validation errors (e.g., "invalid credentials"), iterate over the form and display `form.non_field_errors` and `f.errors`.
        ```html
        {% extends 'base.html' %}

        {% block content %}
        <h1>Авторизация</h1>
        <form method="post">
            {% csrf_token %}
            <div class="form-error">{{ form.non_field_errors }}</div>
            {{ form.as_p }}
            <p><button type="submit">Войти</button></p>
        </form>
        {% endblock %}
        ```

3.  **Implement Logout:**
    * Use Django's built-in `logout` function for the logout view in `users/views.py`.
    * Redirect to the login page after logout. Use the namespace defined earlier (`users:login`).
        ```python
        from django.contrib.auth import logout
        from django.http import HttpResponseRedirect
        from django.urls import reverse

        def logout_user(request):
            logout(request)
            return HttpResponseRedirect(reverse('users:login'))
        ```
    * **Note:** You can also use the class-based `LogoutView` directly in `users/urls.py` for a simpler implementation.

---

#### **Part 3: Page Access Control**

1.  **Protect Views:**
    * To restrict access to function-based views for unauthenticated users, use the `@login_required` decorator.
    * For class-based views, inherit from the `LoginRequiredMixin`. This must be the first class inherited.
        ```python
        # Class-based view example
        from django.contrib.auth.mixins import LoginRequiredMixin
        from django.views.generic import CreateView

        class AddPage(LoginRequiredMixin, CreateView):
            # ... view logic
            login_url = reverse_lazy('users:login') # Optional: view-specific login URL
        ```

2.  **Configure Login URL:**
    * When a user tries to access a protected page, Django redirects them to the login form.
    * You must tell Django where your login page is. In `settings.py`, add:
        ```python
        LOGIN_URL = 'users:login'
        ```
    * Django will automatically append a `?next=/protected-page/` parameter to the URL, ensuring the user is redirected back to their intended page after logging in.

---

#### **Part 4: Email-Based Authentication**

1.  **Create a Custom Authentication Backend:**
    * Create a new file: `users/authentication.py`.
    * Define a class that inherits from `BaseBackend`. It must implement `authenticate()` and `get_user()`.
    * The `authenticate` method will try to fetch a user by `email` (passed in the `username` parameter) and verify their password.
    * The `get_user` method retrieves the user by their ID, which is necessary for maintaining the login session.
        ```python
        from django.contrib.auth import get_user_model
        from django.contrib.auth.backends import BaseBackend

        class EmailAuthBackend(BaseBackend):
            def authenticate(self, request, username=None, password=None, **kwargs):
                user_model = get_user_model()
                try:
                    user = user_model.objects.get(email=username)
                    if user.check_password(password):
                        return user
                    return None
                except user_model.DoesNotExist:
                    return None

            def get_user(self, user_id):
                user_model = get_user_model()
                try:
                    return user_model.objects.get(pk=user_id)
                except user_model.DoesNotExist:
                    return None
        ```

2.  **Activate the Backend:**
    * In `settings.py`, add your new backend to the `AUTHENTICATION_BACKENDS` list. Keep the default `ModelBackend` to allow users to log in with either their username or email.
        ```python
        AUTHENTICATION_BACKENDS = [
            'django.contrib.auth.backends.ModelBackend',
            'users.authentication.EmailAuthBackend',
        ]
        ```

---

#### **Part 5: User Profile and Password Management**

1.  **Create the Profile View and Template:**
    * Use a class-based view inheriting from `LoginRequiredMixin` and `UpdateView`.
    * To ensure users can only edit their own profile, override the `get_object` method to return `self.request.user`. 
    * Create a corresponding template `users/profile.html` with a form.
        ```python
        # users/views.py
        class ProfileUser(LoginRequiredMixin, UpdateView):
            model = get_user_model()
            form_class = ProfileUserForm # You will create this form
            template_name = 'users/profile.html'
            extra_context = {'title': "Профиль пользователя"}

            def get_success_url(self):
                return reverse_lazy('users:profile')

            def get_object(self, queryset=None):
                return self.request.user
        ```
    * Add the URL to `users/urls.py`: `path('profile/', views.ProfileUser.as_view(), name='profile'),`.

2.  **Implement Password Change:**
    * Use Django's built-in `PasswordChangeView` and `PasswordChangeDoneView`.
    * Add their routes to `users/urls.py`. You can customize them with your own templates.
        ```python
        # users/urls.py
        from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView

        path('password-change/',
             PasswordChangeView.as_view(template_name="users/password_change_form.html",
                                        success_url=reverse_lazy("users:password_change_done")),
             name='password_change'),
        path('password-change/done/',
             PasswordChangeDoneView.as_view(template_name="users/password_change_done.html"),
             name='password_change_done'),
        ```
    * Add a link to the `users:password_change` URL from the user's profile template.

---

#### **Part 6: Password Reset via Email**

1.  **Configure Email Backend:**
    * For development, configure the console backend in `settings.py` to print emails to the console.
        ```python
        EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
        ```
    * For production, configure the SMTP backend with credentials from your email provider (Yandex).
        ```python
        EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
        EMAIL_HOST = "smtp.yandex.ru"
        EMAIL_PORT = 465
        EMAIL_HOST_USER = "your-email@yandex.ru"
        EMAIL_HOST_PASSWORD = "your-app-password"
        EMAIL_USE_SSL = True
        DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
        ```

2.  **Implement Password Reset Flow:**
    * This process uses four built-in views: `PasswordResetView`, `PasswordResetDoneView`, `PasswordResetConfirmView`, and `PasswordResetCompleteView`.
    * Add URL patterns for all four views in `users/urls.py`. You *must* provide custom templates and correctly namespaced `success_url`s.
        ```python
        # users/urls.py
        from django.contrib.auth import views as auth_views

        # ...
        path('password-reset/',
             auth_views.PasswordResetView.as_view(
                 template_name="users/password_reset_form.html",
                 email_template_name="users/password_reset_email.html",
                 success_url=reverse_lazy("users:password_reset_done")
             ),
             name='password_reset'),
        path('password-reset/done/',
             auth_views.PasswordResetDoneView.as_view(template_name="users/password_reset_done.html"),
             name='password_reset_done'),
        path('password-reset/<uidb64>/<token>/',
             auth_views.PasswordResetConfirmView.as_view(
                 template_name="users/password_reset_confirm.html",
                 success_url=reverse_lazy("users:password_reset_complete")
             ),
             name='password_reset_confirm'),
        path('password-reset/complete/',
             auth_views.PasswordResetCompleteView.as_view(template_name="users/password_reset_complete.html"),
             name='password_reset_complete'),
        ```
    * Create the four corresponding HTML templates.
    * **Crucially**, in your `password_reset_email.html` template, the link to confirm the reset must use the full namespace: `{% url 'users:password_reset_confirm' uidb64=uid token=token %}`. Failure to do so will result in a `NoReverseMatch` error.
    * Finally, add a link to the `users:password_reset` URL on your login page.

---

#### **Part 7: Permissions and Groups**

1.  **Restricting Access with Permissions:**
    * Django auto-creates `add`, `change`, `delete`, and `view` permissions for every model.
    * To protect a class-based view, use `PermissionRequiredMixin` and specify the required permission as `app_name.action_modelname`.
        ```python
        # women/views.py example from document
        class AddPage(PermissionRequiredMixin, CreateView):
            permission_required = 'women.add_women'
            # ...
        ```
    * Attempting to access this page without the permission will result in a 403 Forbidden error.

2.  **Using Permissions in Templates:**
    * You can conditionally render content in templates based on a user's permissions. Use the `perms` object that is available in every template context.
        ```html
        {% if perms.women.change_women %}
            <p><a href="#">Редактировать</a></p>
        {% endif %}
        ```

3.  **Using Groups for Role-Based Access:**
    * Instead of assigning multiple permissions to users individually, create a `Group` in the Django admin panel. 
    * Assign a set of permissions to that group (e.g., a "Moderator" group with all content management permissions). 
    * Assign users to the group. They will inherit all permissions from that group.

4.  **Creating Custom Permissions:**
    * If you need a permission not tied to a model's CRUD actions (e.g., `can_publish_articles`), you can create it programmatically.
        ```python
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.auth import get_user_model

        content_type = ContentType.objects.get_for_model(get_user_model())
        permission = Permission.objects.create(
            codename="can_publish_articles",
            name="Can Publish Articles",
            content_type=content_type,
        )
        ```
    * This new permission will appear in the admin panel and can be assigned to users or groups.