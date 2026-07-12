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
import re
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
    TAG_NAME_RE = re.compile(r"#?[A-Za-z0-9_-]+")

    """
    Form for creating new blog posts with optional cover image compression.
    """

    tag_names = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "#heart, #love, #relationship"}))

    class Meta:
        model = Post
        fields = ["title", "body", "cover_image"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 10}),
            "cover_image": forms.FileInput(attrs={"class": "form-control"}),
        }

    def clean_tag_names(self):
        raw_value = (self.cleaned_data.get("tag_names") or "").strip()
        if not raw_value:
            return ""

        normalized_input = raw_value.replace("\n", ",").replace("，", ",").replace("；", ",").replace(";", ",")
        if "," in normalized_input:
            parts = [part.strip() for part in normalized_input.split(",") if part.strip()]
        else:
            parts = ["".join(normalized_input.split())]

        cleaned_tags = []
        seen = set()
        for part in parts:
            compact = "".join(part.split())
            if not compact:
                continue
            if not self.TAG_NAME_RE.fullmatch(compact):
                raise ValidationError("Each tag must contain only letters, numbers, underscores, or hyphens.")
            if not compact.startswith("#"):
                compact = f"#{compact}"
            normalized = compact.lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            cleaned_tags.append(normalized)

        return ", ".join(cleaned_tags)

    def _normalized_tag_list(self):
        tags_value = self.cleaned_data.get("tag_names", "")
        return [tag.strip() for tag in tags_value.split(",") if tag.strip()]

    def save(self, commit=True):
        post = super().save(commit=commit)
        if commit:
            post.tags.set(self._normalized_tag_list())
        else:
            self._pending_tags = self._normalized_tag_list()
        return post

    def _save_m2m(self):
        if getattr(self, "instance", None) and getattr(self.instance, "pk", None):
            pending_tags = getattr(self, "_pending_tags", None)
            if pending_tags is not None:
                self.instance.tags.set(pending_tags)

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

class PostEditForm(PostCreateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and getattr(self.instance, "pk", None):
            self.initial["tag_names"] = ", ".join(tag.name for tag in self.instance.tags.all())



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




class AudioEditFileInput(forms.ClearableFileInput):
    template_name = "widgets/audio_clearable_file_input.html"
    initial_text = "Current audio file"
    input_text = "Choose replacement audio file"
    clear_checkbox_label = "Remove current audio file"


class AudioEditCoverInput(forms.ClearableFileInput):
    template_name = "widgets/audio_clearable_file_input.html"
    initial_text = "Current cover image"
    input_text = "Choose replacement cover image"
    clear_checkbox_label = "Remove current cover image"


class AudioUploadForm(forms.ModelForm):
    """
    Form for uploading audio files.
    Includes validation for file type and size.
    """

    audio_file = AudioMultipleFileField(
        required=False,
        widget=AudioMultipleFileInput(attrs={"accept": ".mp3,.wav,.ogg,audio/mpeg,audio/mp3,audio/wav,audio/x-wav,audio/ogg"}),
    )

    class Meta:
        model = AudioPost
        fields = ["music_name", "audio_file", "cover_image", "description"]
        widgets = {
            "music_name": forms.TextInput(attrs={"placeholder": "Required for single upload"}),
            "cover_image": AudioEditCoverInput(attrs={"accept": ".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"}),
            "description": forms.Textarea(attrs={"row": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        audio_files = cleaned_data.get("audio_file") or []
        music_name = (cleaned_data.get("music_name") or "").strip()

        if audio_files and len(audio_files) == 1 and not music_name:
            self.add_error("music_name", "Track title is required when uploading a single audio file.")

        return cleaned_data

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

class AudioPostEditForm(forms.ModelForm):
    audio_file = forms.FileField(
        required=False,
        widget=AudioEditFileInput(attrs={"accept": ".mp3,.wav,.ogg,audio/mpeg,audio/mp3,audio/wav,audio/x-wav,audio/ogg"}),
    )

    class Meta:
        model = AudioPost
        fields = ["music_name", "audio_file", "cover_image", "description"]
        widgets = {
            "music_name": forms.TextInput(),
            "cover_image": forms.FileInput(attrs={"accept": ".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"}),
            "description": forms.Textarea(attrs={"row": 3}),
        }

    def clean_audio_file(self):
        audio_file = self.cleaned_data.get("audio_file")
        if not audio_file or not hasattr(audio_file, "content_type"):
            return self.instance.audio_file
        return AudioUploadForm.validate_audio_upload(audio_file)

    def clean_cover_image(self):
        image = self.cleaned_data.get("cover_image")
        if not image or not hasattr(image, "content_type"):
            return self.instance.cover_image

        allowed_types = {"image/jpeg", "image/png", "image/webp"}
        allowed_extensions = (".jpg", ".jpeg", ".png", ".webp")
        if getattr(image, "content_type", "") not in allowed_types:
            raise ValidationError("Cover image must be a JPEG, PNG, or WebP image.")
        if not image.name.lower().endswith(allowed_extensions):
            raise ValidationError("Cover image extension must be .jpg, .jpeg, .png, or .webp.")
        if image.size > 3 * 1024 * 1024:
            raise ValidationError("Cover image must be 3MB or smaller.")
        return image





class VideoPostEditForm(forms.ModelForm):
    video_file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={"accept": ".mp4,.webm,.mov,video/mp4,video/webm,video/quicktime"}),
    )

    class Meta:
        model = VideoPost
        fields = ["title", "video_file", "description"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Video title"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_video_file(self):
        video_file = self.cleaned_data.get("video_file")
        if not video_file or not hasattr(video_file, "content_type"):
            return self.instance.video_file
        return VideoUploadForm.validate_video_file(video_file)

class VideoUploadForm(forms.ModelForm):
    class Meta:
        model = VideoPost
        fields = ["title", "video_file", "description"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Optional title"}),
            "video_file": forms.FileInput(attrs={"accept": ".mp4,.webm,.mov,video/mp4,video/webm,video/quicktime"}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    @staticmethod
    def validate_video_file(video_file):
        allowed_types = {"video/mp4", "video/webm", "video/quicktime"}
        allowed_extensions = (".mp4", ".webm", ".mov")
        if getattr(video_file, "content_type", "") not in allowed_types:
            raise ValidationError("Video upload must be an MP4, WebM, or MOV file.")
        if not video_file.name.lower().endswith(allowed_extensions):
            raise ValidationError("Video file extension must be .mp4, .webm, or .mov.")
        if video_file.size > 200 * 1024 * 1024:
            raise ValidationError("Video upload must be 200MB or smaller.")
        return video_file

    def clean_video_file(self):
        video_file = self.cleaned_data.get("video_file")
        if not video_file:
            raise ValidationError("Please choose a video file.")
        return self.validate_video_file(video_file)
