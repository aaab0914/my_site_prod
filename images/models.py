from django.db import models
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile

import os
import sys


class ImagePost(models.Model):
    """
    Model for managing uploaded images.
    """
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='posts/%Y/%m/%d/')
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # 直接调用父类的 save()，不进行任何压缩
        super().save(*args, **kwargs)