from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


class ImagePost(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to="posts/%Y/%m/%d/")
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if self.image and self.image.size > 25 * 1024 * 1024:
            raise ValidationError({
                "image": f"图片文件大小不能超过 25MB。当前文件大小: {self.image.size / (1024 * 1024):.2f}MB"
            })

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def get_image_proxy_url(self):
        if not self.image:
            return ""
        return reverse("blog:images:gallery_media", args=[self.pk])


class Album(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="albums")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]
        indexes = [models.Index(fields=["created"])]

    def __str__(self):
        return self.title

    def cover_image(self):
        return self.images.order_by('id').first()

    def image_count(self):
        return self.images.count()


class AlbumImage(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name="images", null=True, blank=True)
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to="albums/%Y/%m/%d/")
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="album_images")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created", "id"]
        indexes = [models.Index(fields=["created"])]

    def __str__(self):
        return self.title

    def get_image_proxy_url(self):
        if not self.image:
            return ""
        return reverse("blog:images:album_media", args=[self.pk])
