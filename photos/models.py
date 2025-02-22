from django.db import models
from django.contrib.auth.models import User

class Photo(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='photos/')
    description = models.TextField()
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # Делаем поле необязательным
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title