from django import forms
from .models import Photo, Category, Comment


class PhotoForm(forms.ModelForm):
    tags = forms.CharField(
        required=False, 
        widget=forms.TextInput(attrs={'placeholder': 'Введите теги через запятую'}),
        help_text='Введите теги через запятую, например: природа, горы, закат'
    )
    
    class Meta:
        model = Photo
        # Удаляем поле category из формы
        fields = ['title', 'image', 'description', 'category_type']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If we're editing an existing photo, populate the tags field
        if self.instance.pk:
            self.initial['tags'] = ', '.join([tag.name for tag in self.instance.tags.all()])
            
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if commit:
            instance.save()
            
            # Handle tags with taggit - only after the instance has been saved
            if 'tags' in self.cleaned_data:
                # Clear existing tags
                instance.tags.clear()
                
                # Add new tags
                tag_string = self.cleaned_data['tags']
                if tag_string:
                    tag_list = [tag.strip() for tag in tag_string.split(',') if tag.strip()]
                    instance.tags.add(*tag_list)
        
        return instance

class CategoryForm(forms.ModelForm):

    class Meta:
        model = Category
        fields = ['name', 'description']


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text':
            forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Введите ваш комментарий'
            })
        }
