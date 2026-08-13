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

from .models import Post, Comment, AudioPost, VideoPost
from taggit.forms import TagWidget


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
            "tags": TagWidget(attrs={"class": "form-control"}),
        }

    def clean_cover_image(self):
        image = self.cleaned_data.get("cover_image")
        if image:
            allowed_types = {"image/jpeg", "image/png", "image/webp"}
            if getattr(image, "content_type", "") not in allowed_types:
                raise ValidationError("Cover image must be a JPEG, PNG, or WebP image.")
            if image.size > 3 * 1024 * 1024:
                raise ValidationError("Cover image must be 3MB or smaller before optimization.")
            img = Image.open(image)
            if hasattr(image, "seek"):
                image.seek(0)
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")

            max_width = 1600
            max_height = 1600
            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            img_io = BytesIO()
            img.save(img_io, format="JPEG", quality=82, optimize=False, progressive=False)

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

class AudioMultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class AudioMultipleFileField(forms.FileField):
    def clean(self, data, initial=None):
        if not data:
            if initial:
                return initial
            if self.required:
                raise ValidationError("Please choose at least one audio file.")
            return []

        files = data if isinstance(data, (list, tuple)) else [data]
        return [super(AudioMultipleFileField, self).clean(file, initial) for file in files]


class AudioUploadForm(forms.ModelForm):
    """
    Form for uploading audio files.
    Includes validation for file type and size.
    """

    audio_file = AudioMultipleFileField(
        required=False,
        widget=AudioMultipleFileInput(attrs={"accept": ".mp3,.wav,.ogg,audio/*"}),
    )

    class Meta:
        model = AudioPost
        fields = ["music_name", "audio_file", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"row": 3}),
        }

    @staticmethod
    def validate_audio_upload(audio_file):
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
        if audio_file.size > 25 * 1024 * 1024:
            raise ValidationError("Audio upload must be 25MB or smaller.")
        return audio_file

    def clean_audio_file(self):
        """
        Validate newly uploaded audio files.

        When editing an existing AudioPost, leaving the upload field blank keeps
        the current file and must not trigger upload validation.
        """
        audio_files = self.cleaned_data.get("audio_file")
        if not audio_files:
            return audio_files

        if not isinstance(audio_files, (list, tuple)):
            audio_files = [audio_files]

        validated = []
        for audio_file in audio_files:
            if not hasattr(audio_file, "content_type"):
                validated.append(audio_file)
                continue
            validated.append(self.validate_audio_upload(audio_file))
        return validated



class VideoUploadForm(forms.ModelForm):
    """Form for uploading a single video file."""

    class Meta:
        model = VideoPost
        fields = ["title", "video_file", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"row": 3}),
        }

    def clean_video_file(self):
        video_file = self.cleaned_data.get("video_file")
        if not video_file:
            raise ValidationError("Please choose a video file.")

        allowed_types = {
            "video/mp4",
            "video/webm",
            "video/ogg",
            "application/octet-stream",
        }
        allowed_extensions = (".mp4", ".webm", ".ogg", ".mov", ".m4v")
        content_type = getattr(video_file, "content_type", "")
        if content_type and content_type not in allowed_types and not video_file.name.lower().endswith(allowed_extensions):
            raise ValidationError("Video upload must be an MP4, WebM, OGG, MOV, or M4V file.")
        if not video_file.name.lower().endswith(allowed_extensions):
            raise ValidationError("Video file extension must be .mp4, .webm, .ogg, .mov, or .m4v.")
        if video_file.size > 200 * 1024 * 1024:
            raise ValidationError("Video upload must be 200MB or smaller.")
        return video_file
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
