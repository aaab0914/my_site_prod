import base64
import binascii
import json
from io import BytesIO

from PIL import Image, UnidentifiedImageError
from django import forms
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile, SimpleUploadedFile

from .models import Album, AlbumImage, ImagePost


class ImagePostForm(forms.ModelForm):
    class Meta:
        model = ImagePost
        fields = ["title", "image", "description"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
        }

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image:
            return optimize_uploaded_image(image)
        return image


class MultipleImageInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class AlbumMultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class AlbumMultipleFileField(forms.FileField):
    def clean(self, data, initial=None):
        if not data:
            if self.required:
                raise ValidationError("Please choose at least one image.")
            return []

        files = data if isinstance(data, (list, tuple)) else [data]
        cleaned = []
        for file in files:
            cleaned.append(super().clean(file, initial))
        return cleaned


class GalleryUploadForm(forms.Form):
    images = forms.CharField(
        required=False,
        widget=MultipleImageInput(attrs={"class": "form-control", "accept": "image/*"}),
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 4}),
    )
    pasted_images_data = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean_images(self):
        return self.extract_uploads()

    def extract_uploads(self):
        file_uploads = list(self.files.getlist("images"))
        pasted_uploads = self._decode_pasted_images()
        all_uploads = file_uploads + pasted_uploads

        if not all_uploads:
            raise ValidationError("Please upload at least one image.")
        if len(all_uploads) > 99:
            raise ValidationError("You can upload at most 99 images at one time.")

        optimized_uploads = []
        for image in all_uploads:
            optimized_uploads.append(optimize_uploaded_image(image))

        return optimized_uploads

    def build_title(self, image, index):
        base_name = image.name.rsplit(".", 1)[0].strip() or "gallery-image"
        return f"{base_name[:180]}-{index}"

    def _decode_pasted_images(self):
        raw_value = self.data.get("pasted_images_data", "").strip()
        if not raw_value:
            return []

        try:
            items = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            raise ValidationError("Pasted image data is invalid.") from exc

        uploads = []
        for index, item in enumerate(items, start=1):
            data_url = item.get("data_url", "")
            if ";base64," not in data_url:
                raise ValidationError("Pasted image data is invalid.")

            header, encoded = data_url.split(";base64,", 1)
            mime_type = header.replace("data:", "", 1).strip().lower()
            if mime_type not in {"image/jpeg", "image/png", "image/webp"}:
                raise ValidationError("Image must be a JPEG, PNG, or WebP file.")

            try:
                encoded = encoded.replace(" ", "+")
                content = base64.b64decode(encoded)
            except (binascii.Error, ValueError) as exc:
                raise ValidationError("Pasted image data is invalid.") from exc

            extension = mime_type.split("/")[-1]
            uploads.append(
                SimpleUploadedFile(
                    item.get("name") or f"pasted-image-{index}.{extension}",
                    content,
                    content_type=mime_type,
                )
            )

        return uploads




class AlbumUploadForm(forms.Form):
    title = forms.CharField(max_length=200)
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 4}))
    images = AlbumMultipleFileField(widget=AlbumMultipleFileInput(attrs={"accept": "image/*"}))

    def clean_images(self):
        files = self.files.getlist("images")
        if not files:
            raise ValidationError("Please choose at least one image.")
        for image in files:
            content_type = getattr(image, "content_type", "")
            if content_type and not content_type.startswith("image/"):
                raise ValidationError("All album uploads must be image files.")
            if image.size > 5 * 1024 * 1024:
                raise ValidationError("Each image must be 5MB or smaller.")
        return files
class GalleryImageEditForm(forms.ModelForm):
    class Meta:
        model = ImagePost
        fields = ["title", "description"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 6}),
        }


def optimize_uploaded_image(image):
    allowed_types = {"image/jpeg", "image/png", "image/webp"}
    if getattr(image, "content_type", "") not in allowed_types:
        raise ValidationError("Image must be a JPEG, PNG, or WebP file.")

    if image.size > 5 * 1024 * 1024:
        raise ValidationError("Image must be 5MB or smaller before optimization.")

    try:
        if hasattr(image, "seek"):
            image.seek(0)
        img = Image.open(image)
        img.load()
    except UnidentifiedImageError as exc:
        raise ValidationError("Uploaded image data is invalid or corrupted.") from exc

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
    output_name = image.name.rsplit(".", 1)[0] + ".jpg"
    return InMemoryUploadedFile(
        img_io,
        "ImageField",
        output_name,
        "image/jpeg",
        img_io.tell(),
        None,
    )
