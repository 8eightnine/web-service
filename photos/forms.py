from django import forms
from .models import Photo, Category, PhotoCategory

class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['title', 'image', 'description', 'category']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #self.fields['category_type'].choices = PhotoCategory.choices()

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
