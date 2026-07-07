from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class ImagePost(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='posts/%Y/%m/%d/')
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.image:
            if self.image.size > 25 * 1024 * 1024:
                raise ValidationError({
                    'image': f"图片文件大小不能超过 25MB。当前文件大小: {self.image.size / (1024 * 1024):.2f}MB"
                })

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
