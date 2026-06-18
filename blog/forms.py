# forms.py
# ========================================
# Imports
# ========================================

from django import forms
# forms: Django's form handling module for creating and validating forms

from .models import Post, Comment, AudioPost
# Comment: The comment model (imported from the current app)
# Post: The main blog post model (imported from the current app)


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
        fields = ['body', 'image']
        widgets = {
            # 'name': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
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
        fields = ['title', 'body', 'tags', 'cover_image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'tags': forms.TextInput(attrs={'class': 'form-control'}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class AudioUploadForm(forms.ModelForm):
    class Meta:
        model = AudioPost
        fields = ['title', 'audio_file', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'row':3}),
        }