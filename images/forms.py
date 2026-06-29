from django import forms
from django.core.exceptions import ValidationError
from .models import ImagePost
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile

class ImagePostForm(forms.ModelForm):
    class Meta:
        model = ImagePost
        fields = ['title', 'image', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            allowed_types = {"image/jpeg", "image/png", "image/webp"}
            if getattr(image, "content_type", "") not in allowed_types:
                raise ValidationError("Image must be a JPEG, PNG, or WebP file.")
            if image.size > 3 * 1024 * 1024:
                raise ValidationError("Image must be 3MB or smaller before optimization.")
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
