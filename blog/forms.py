from io import BytesIO

from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image
from taggit.forms import TagWidget

from my_site.upload_limits import VIDEO_MAX_SIZE

from .models import AudioPost, Comment, Post, VideoPost


class EmailPostForm(forms.Form):
    name = forms.CharField(max_length=25)
    email = forms.EmailField()
    to = forms.EmailField()
    comment = forms.CharField(required=False, widget=forms.Textarea)


class SearchForm(forms.Form):
    query = forms.CharField()


class PostCreateForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "body", "cover_image", "tags"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 10}),
            "cover_image": forms.FileInput(attrs={"class": "form-control"}),
            "tags": TagWidget(attrs={"class": "form-control"}),
        }

    def clean_tags(self):
        tags = self.cleaned_data.get("tags")
        if not tags:
            return tags
        normalized = []
        for tag in tags:
            name = getattr(tag, "name", str(tag)).strip()
            if name and not name.startswith("#"):
                name = f"#{name}"
            if name:
                normalized.append(name)
        return normalized

    def clean_cover_image(self):
        image = self.cleaned_data.get("cover_image")
        if image:
            allowed_types = {"image/jpeg", "image/png", "image/webp"}
            if getattr(image, "content_type", "") not in allowed_types:
                raise ValidationError("Cover image must be a JPEG, PNG, or WebP image.")
            if image.size > 10 * 1024 * 1024:
                raise ValidationError(
                    "Cover image must be 10MB or smaller before optimization."
                )
            img = Image.open(image)
            if hasattr(image, "seek"):
                image.seek(0)
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")
            max_width = max_height = 1600
            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            img_io = BytesIO()
            img.save(
                img_io, format="JPEG", quality=82, optimize=False, progressive=False
            )
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


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(
                attrs={"class": "form-control", "rows": 4, "style": "resize: none;"}
            )
        }


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
        return [
            super(AudioMultipleFileField, self).clean(file, initial) for file in files
        ]


class AudioUploadForm(forms.ModelForm):
    audio_file = AudioMultipleFileField(
        required=False,
        widget=AudioMultipleFileInput(attrs={"accept": ".mp3,.wav,.ogg,audio/*"}),
    )

    class Meta:
        model = AudioPost
        fields = ["music_name", "audio_file", "description"]
        widgets = {"description": forms.Textarea(attrs={"row": 3})}

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
        if audio_file.size > 30 * 1024 * 1024:
            raise ValidationError("Audio upload must be 30MB or smaller.")
        return audio_file

    def clean_audio_file(self):
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


class AudioEditForm(forms.ModelForm):
    class Meta:
        model = AudioPost
        fields = ["music_name", "audio_file", "cover_image", "description"]
        widgets = {
            "audio_file": forms.FileInput(attrs={"accept": ".mp3,.wav,.ogg,audio/*"}),
            "cover_image": forms.ClearableFileInput(
                attrs={"accept": ".jpg,.jpeg,.png,.webp,image/*"}
            ),
            "description": forms.Textarea(attrs={"row": 3}),
        }

    def clean_audio_file(self):
        audio_file = self.cleaned_data.get("audio_file")
        if not audio_file or not hasattr(audio_file, "content_type"):
            return audio_file
        return AudioUploadForm.validate_audio_upload(audio_file)

    def clean_cover_image(self):
        cover_image = self.cleaned_data.get("cover_image")
        if not cover_image or not hasattr(cover_image, "content_type"):
            return cover_image
        allowed_types = {"image/jpeg", "image/png", "image/webp"}
        allowed_extensions = (".jpg", ".jpeg", ".png", ".webp")
        if getattr(cover_image, "content_type", "") not in allowed_types:
            raise ValidationError("Cover image must be a JPEG, PNG, or WebP image.")
        if not cover_image.name.lower().endswith(allowed_extensions):
            raise ValidationError(
                "Cover image extension must be .jpg, .jpeg, .png, or .webp."
            )
        if cover_image.size > 10 * 1024 * 1024:
            raise ValidationError("Cover image must be 10MB or smaller.")
        return cover_image


class VideoUploadForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].help_text = "Maximum 50 characters."
        self.fields["description"].help_text = "Maximum 500 characters."

    class Meta:
        model = VideoPost
        fields = ["title", "video_file", "description"]
        widgets = {
            "video_file": forms.FileInput(),
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_video_file(self):
        video_file = self.cleaned_data.get("video_file")
        if not video_file:
            if self.instance and self.instance.pk and self.instance.video_file:
                return self.instance.video_file
            raise ValidationError("Please choose a video file.")
        allowed_types = {
            "video/mp4",
            "video/webm",
            "video/ogg",
            "application/octet-stream",
        }
        allowed_extensions = (".mp4", ".webm", ".ogg", ".mov", ".m4v")
        content_type = getattr(video_file, "content_type", "")
        if (
            content_type
            and content_type not in allowed_types
            and not video_file.name.lower().endswith(allowed_extensions)
        ):
            raise ValidationError(
                "Video upload must be an MP4, WebM, OGG, MOV, or M4V file."
            )
        if not video_file.name.lower().endswith(allowed_extensions):
            raise ValidationError(
                "Video file extension must be .mp4, .webm, .ogg, .mov, or .m4v."
            )
        if video_file.size > VIDEO_MAX_SIZE:
            raise ValidationError("Video upload must be 100MB or smaller.")
        return video_file
