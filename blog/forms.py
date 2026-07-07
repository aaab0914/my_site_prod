"""
Form definitions for the blog application.

This module provides all form classes used for post creation, searching,
commenting, and audio uploads. It includes custom validation for file uploads
and image compression logic.
"""

# =============================================================================
# IMPORTS (All imports moved to the top)
# =============================================================================

from io import BytesIO
# BytesIO: In-memory buffer for binary data, used to store compressed images.

from django import forms
# forms: Django's form framework. Provides Form, ModelForm, and field types.

from django.core.exceptions import ValidationError
# ValidationError: Exception raised when form data fails validation.

from django.core.files.uploadedfile import InMemoryUploadedFile
# InMemoryUploadedFile: Wrapper for uploaded files stored in memory (not on disk).

from PIL import Image
# PIL.Image: Python Imaging Library, used for opening and processing image files.

from .models import Post, Comment, AudioPost


# Post: The main blog post model.
# Comment: User comments attached to posts.
# AudioPost: Audio file uploads associated with the blog.


# =============================================================================
# POST FORMS
# =============================================================================

class EmailPostForm(forms.Form):
    """
    Form for sharing a post via email (currently a placeholder).
    """
    name = forms.CharField(max_length=25)
    # name: The sender's name (max 25 characters).

    email = forms.EmailField()
    # email: The sender's email address.

    to = forms.EmailField()
    # to: The recipient's email address.

    comment = forms.CharField(required=False, widget=forms.Textarea)
    # comment: Optional personal message to include in the email.


class SearchForm(forms.Form):
    """
    Form for capturing user search queries.
    """
    query = forms.CharField()
    # query: The search term entered by the user.


class PostCreateForm(forms.ModelForm):
    """
    Form for creating new blog posts with optional cover image compression.
    """

    class Meta:
        model = Post
        fields = ["title", "body", "cover_image", "tags"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 10}),
            "cover_image": forms.FileInput(attrs={"class": "form-control"}),
            "tags": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_cover_image(self):
        """
        Validate and compress the uploaded cover image.

        Returns:
            InMemoryUploadedFile: The compressed JPEG image, or None if no image.
        """
        image = self.cleaned_data.get("cover_image")
        if image:
            allowed_types = {"image/jpeg", "image/png", "image/webp"}
            if getattr(image, "content_type", "") not in allowed_types:
                raise ValidationError("Cover image must be a JPEG, PNG, or WebP image.")
            if image.size > 3 * 1024 * 1024:
                raise ValidationError("Cover image must be 3MB or smaller before optimization.")
            img = Image.open(image)
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")

            max_size = 1.5 * 1024 * 1024
            quality = 85
            img_io = BytesIO()

            while quality > 30:
                img_io.seek(0)
                img_io.truncate()
                img.save(img_io, format="JPEG", quality=quality, optimize=True)
                if img_io.tell() <= max_size:
                    break
                quality -= 5

            scale = 1.0
            while img_io.tell() > max_size and scale > 0.5:
                scale -= 0.1
                width, height = img.size
                new_size = (int(width * scale), int(height * scale))
                img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
                img_io = BytesIO()
                img_resized.save(img_io, format="JPEG", quality=quality, optimize=True)

            img_io.seek(0)
            return InMemoryUploadedFile(
                img_io,
                "ImageField",
                image.name.split(".")[0] + ".jpg",
                "image/jpeg",
                img_io.tell(),
                None,
            )
        return image


# =============================================================================
# COMMENT FORMS
# =============================================================================

class CommentForm(forms.ModelForm):
    """
    Form for adding comments to blog posts.
    """

    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }


# =============================================================================
# AUDIO FORMS
# =============================================================================

class AudioUploadForm(forms.ModelForm):
    """
    Form for uploading audio files.
    Includes validation for file type and size.
    """

    class Meta:
        model = AudioPost
        fields = ["music_name", "audio_file", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"row": 3}),
        }

    def clean_audio_file(self):
        """
        Validate the uploaded audio file for type and size.

        Returns:
            UploadedFile: The validated audio file object.
        """
        audio_file = self.cleaned_data.get("audio_file")
        if not audio_file:
            return audio_file
        allowed_types = {
            "audio/mpeg",
            "audio/mp3",
            "audio/wav",
            "audio/x-wav",
            "audio/ogg",
        }
        allowed_extensions = (".mp3", ".wav", ".ogg")
        if getattr(audio_file, "content_type", "") not in allowed_types:
            raise ValidationError("Audio upload must be an MP3, WAV, or OGG file.")
        if not audio_file.name.lower().endswith(allowed_extensions):
            raise ValidationError("Audio file extension must be .mp3, .wav, or .ogg.")
        if audio_file.size > 10 * 1024 * 1024:
            raise ValidationError("Audio upload must be 10MB or smaller.")
        return audio_file

# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                         blog/forms.py                                      │
# │                  (Form Definitions for Blog App)                           │
# └─────────────────────────────────────────────────────────────────────────────┘
#                                       │
#                                       ▼
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                            IMPORTS (Dependencies)                           │
# ├─────────────────────────────────────────────────────────────────────────────┤
# │  io.BytesIO                 │  django.forms          │  PIL.Image          │
# │  django.core.exceptions     │  ├─ Form               │  .models            │
# │  ├─ ValidationError         │  ├─ ModelForm          │  ├─ Post            │
# │  django.core.files          │  ├─ fields             │  ├─ Comment         │
# │  └─ uploadedfile            │  ├─ widgets            │  └─ AudioPost      │
# │      └─ InMemoryUploadedFile│  └─ ModelForm          │                     │
# └─────────────────────────────────────────────────────────────────────────────┘
#                                       │
#                                       ▼
#                  ┌────────────────────────────────────────────────┐
#                  │            Form Classes                       │
#                  └────────────────────────────────────────────────┘
#                                       │
#          ┌────────────────────────────┼────────────────────────────┐
#          │                            │                            │
#          ▼                            ▼                            ▼
# ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
# │   EmailPostForm      │  │   SearchForm          │  │   PostCreateForm     │
# │   (Class)            │  │   (Class)            │  │   (Class)            │
# ├──────────────────────┤  ├──────────────────────┤  ├──────────────────────┤
# │ Inherits:            │  │ Inherits:            │  │ Inherits:            │
# │   forms.Form         │  │   forms.Form         │  │   forms.ModelForm    │
# │                      │  │                      │  │                      │
# │ Purpose:             │  │ Purpose:             │  │ Purpose:             │
# │   Share post via     │  │   Capture search     │  │   Create new posts   │
# │   email (placeholder)│  │   query from user    │  │                      │
# │                      │  │                      │  │ Custom Validation:   │
# │ Fields:              │  │ Fields:              │  │   clean_cover_image():│
# │   name               │  │   query              │  │   - Validate type   │
# │   email              │  │                      │  │   - Compress to JPEG│
# │   to                 │  │                      │  │   - Resize if needed│
# │   comment            │  │                      │  │   - Return optimized│
# │                      │  │                      │  │     JPEG in memory  │
# └──────────────────────┘  └──────────────────────┘  └──────────────────────┘
#                                       │
#          ┌────────────────────────────┼────────────────────────────┐
#          ▼                            ▼                            ▼
# ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
# │   CommentForm        │  │   AudioUploadForm     │  │                      │
# │   (Class)            │  │   (Class)            │  │                      │
# ├──────────────────────┤  ├──────────────────────┤  │                      │
# │ Inherits:            │  │ Inherits:            │  │                      │
# │   forms.ModelForm    │  │   forms.ModelForm    │  │                      │
# │                      │  │                      │  │                      │
# │ Purpose:             │  │ Purpose:             │  │                      │
# │   Add comments to    │  │   Upload audio files │  │                      │
# │   posts              │  │                      │  │                      │
# │                      │  │ Custom Validation:   │  │                      │
# │ Fields:              │  │   clean_audio_file():│  │                      │
# │   body (textarea)    │  │   - Validate type    │  │                      │
# │                      │  │   - Validate extension│  │                      │
# │                      │  │   - Validate size    │  │                      │
# │                      │  │     (max 10MB)       │  │                      │
# └──────────────────────┘  └──────────────────────┘  └──────────────────────┘