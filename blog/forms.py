# forms.py
# ========================================
# Imports
# ========================================

from django import forms
from .models import Post, Comment, AudioPost
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile


# ========================================
# Forms
# ========================================

class EmailPostForm(forms.Form):
    """
    Form for sharing a post via email.
    """
    name = forms.CharField(max_length=25)
    email = forms.EmailField()
    to = forms.EmailField()
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea
    )


class CommentForm(forms.ModelForm):
    """
    Form for adding a comment to a post.
    """
    class Meta:
        model = Comment
        fields = ['body']
        widgets = {
            # 'name': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            # 'image': forms.FileInput(attrs={'class': 'form-control'}),
        }


class SearchForm(forms.Form):
    """
    Form for searching posts by keyword.
    """
    query = forms.CharField()


class PostCreateForm(forms.ModelForm):
    """
    Form for creating a new post.
    """
    class Meta:
        model = Post
        fields = ['title', 'body', 'cover_image', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_cover_image(self):
        image = self.cleaned_data.get('cover_image')
        if image:
            img = Image.open(image)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')

            MAX_SIZE = 1.5 * 1024 * 1024
            quality = 85
            img_io = BytesIO()

            while quality > 30:
                img_io.seek(0)
                img_io.truncate()
                img.save(img_io, format='JPEG', quality=quality, optimize=True)
                if img_io.tell() <= MAX_SIZE:
                    break
                quality -= 5

            scale = 1.0
            while img_io.tell() > MAX_SIZE and scale > 0.5:
                scale -= 0.1
                width, height = img.size
                new_size = (int(width * scale), int(height * scale))
                img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
                img_io = BytesIO()
                img_resized.save(img_io, format='JPEG', quality=quality, optimize=True)

            img_io.seek(0)
            return InMemoryUploadedFile(
                img_io, 'ImageField',
                image.name.split('.')[0] + '.jpg',
                'image/jpeg', img_io.tell(), None
            )
        return image

class AudioUploadForm(forms.ModelForm):
    class Meta:
        model = AudioPost
        fields = ['music_name', 'audio_file', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'row':3}),
        }