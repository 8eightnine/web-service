from django import forms
from .models import Photo, Category, Comment, Tag


class PhotoForm(forms.ModelForm):
    tags = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={'placeholder': 'Введите теги через запятую'}),
        help_text='Введите теги через запятую, например: природа, горы, закат')

    class Meta:
        model = Photo
        fields = ['title', 'image', 'description', 'category', 'category_type']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If we're editing an existing photo, populate the tags field
        if self.instance.pk:
            self.initial['tags'] = ', '.join(
                [tag.name for tag in self.instance.tags.all()])


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


class TagForm(forms.ModelForm):

    class Meta:
        model = Tag
        fields = ['name']
