from django import forms
from .models import Photo, Category, PhotoCategory, Tag, Comment

class PhotoForm(forms.ModelForm):
    tags = forms.CharField(required=False, 
                          help_text="Введите теги через запятую")
    
    class Meta:
        model = Photo
        fields = ['title', 'image', 'description', 'category', 'category_type', 'tags']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            # If editing an existing photo, populate the tags field
            self.initial['tags'] = ', '.join([tag.name for tag in self.instance.tags.all()])
    
    def save(self, commit=True):
        photo = super().save(commit=False)
        
        if commit:
            photo.save()
            
            # Handle tags
            if 'tags' in self.cleaned_data and self.cleaned_data['tags']:
                # Clear existing tags
                photo.tags.clear()
                
                # Process and add new tags
                tag_names = [name.strip() for name in self.cleaned_data['tags'].split(',') if name.strip()]
                for tag_name in tag_names:
                    tag, created = Tag.objects.get_or_create(
                        name=tag_name,
                        defaults={'slug': slugify(tag_name)}
                    )
                    photo.tags.add(tag)
                    
        return photo

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Оставьте комментарий...'})
        }
