import os
from itertools import count

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from markdownx.models import MarkdownxField
from taggit.managers import TaggableManager

from my_site.markdown_utils import render_markdown
from my_site.media_naming import dated_media_upload_to, media_display_name


class PublishedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Post.Status.PUBLISHED)


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DF", "Draft"
        PUBLISHED = "PB", "Published"

    title = models.CharField(max_length=50)
    cover_image = models.ImageField(
        upload_to=dated_media_upload_to("posts"), blank=True, null=True
    )
    slug = models.SlugField(max_length=250, unique_for_date="publish")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blog_posts"
    )
    body = MarkdownxField(max_length=50000)
    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=Status, default=Status.DRAFT)
    tags = TaggableManager()
    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        ordering = ["-publish"]
        indexes = [
            models.Index(fields=["-publish"]),
            models.Index(fields=["-publish", "-id"]),
            models.Index(fields=["slug", "publish"]),
            models.Index(fields=["author", "-publish"]),
            models.Index(fields=["status", "-publish"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["slug", "publish"], name="unique_slug_per_date"
            )
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            "blog:post_detail",
            args=[self.publish.year, self.publish.month, self.publish.day, self.slug],
        )

    def build_slug(self):
        base_slug = slugify(self.title)
        if not base_slug:
            timestamp = timezone.localtime(self.publish or timezone.now()).strftime(
                "%Y%m%d%H%M%S"
            )
            base_slug = f"post-{timestamp}"
        base_slug = base_slug[:250]
        publish_date = timezone.localtime(self.publish or timezone.now()).date()
        existing = Post.objects.filter(publish__date=publish_date)
        if self.pk:
            existing = existing.exclude(pk=self.pk)
        for index in count(1):
            suffix = "" if index == 1 else f"-{index}"
            candidate = f"{base_slug[: 250 - len(suffix)]}{suffix}"
            if candidate and not existing.filter(slug=candidate).exists():
                return candidate
        raise ValueError("Unable to generate a unique slug for the post.")

    def clean(self):
        if self.pk and self.status == self.Status.PUBLISHED and not self.tags.exists():
            raise ValidationError("发布的文章必须包含至少一个标签(tag)。")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.build_slug()
        self.clean()
        super().save(*args, **kwargs)

    def get_markdown_body(self):
        return render_markdown(self.body)

    def get_cover_image_proxy_url(self):
        if not self.cover_image:
            return ""
        return reverse("blog:post_cover_image", args=[self.pk])


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blog_comments"
    )
    email = models.EmailField()
    body = models.CharField(max_length=500)
    image = models.ImageField(
        upload_to=dated_media_upload_to("comments"), blank=True, null=True
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["created"]
        indexes = [models.Index(fields=["created"])]

    def __str__(self):
        preview = (self.body or "").strip().replace("\n", " ")
        if len(preview) > 30:
            preview = f"{preview[:30].rstrip()}..."
        return (
            f"Comment by {self.display_name} on {self.post}: {preview}"
            if preview
            else f"Comment by {self.display_name} on {self.post}"
        )

    @property
    def display_name(self):
        if self.author_id:
            return self.author.username
        return self.email.split("@", 1)[0]

    def get_image_proxy_url(self):
        if not self.image:
            return ""
        return reverse("blog:comment_image", args=[self.pk])


class AudioPost(models.Model):
    audio_file = models.FileField(upload_to=dated_media_upload_to("audio"))
    cover_image = models.ImageField(
        upload_to=dated_media_upload_to("audio/covers"), blank=True, null=True
    )
    description = models.TextField(max_length=500, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="audio_posts"
    )
    music_name = models.CharField(max_length=200, blank=True)
    active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["created"]),
            models.Index(fields=["-created", "-id"]),
            models.Index(fields=["uploaded_by", "-created"]),
        ]

    def __str__(self):
        return self.music_name or media_display_name(self.audio_file)

    def save(self, *args, **kwargs):
        if not self.music_name and self.audio_file:
            self.music_name = os.path.splitext(media_display_name(self.audio_file))[0]
        super().save(*args, **kwargs)

    def get_audio_filename(self):
        if not self.audio_file:
            return ""
        return media_display_name(self.audio_file)

    def get_cover_filename(self):
        if not self.cover_image:
            return ""
        return media_display_name(self.cover_image)

    def get_audio_proxy_url(self):
        if not self.audio_file:
            return ""
        version = (
            int((self.updated or self.created).timestamp())
            if (self.updated or self.created)
            else self.pk
        )
        return f"{reverse('blog:audio_file_proxy', args=[self.pk])}?v={version}"

    def get_cover_image_proxy_url(self):
        if not self.cover_image:
            return ""
        version = (
            int((self.updated or self.created).timestamp())
            if (self.updated or self.created)
            else self.pk
        )
        return f"{reverse('blog:audio_cover_image_proxy', args=[self.pk])}?v={version}"


class VideoPost(models.Model):
    video_file = models.FileField(upload_to=dated_media_upload_to("videos"))
    cover_image = models.ImageField(
        upload_to=dated_media_upload_to("videos"), blank=True, null=True
    )
    title = models.CharField(max_length=50, blank=True)
    description = models.TextField(max_length=500, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="video_posts"
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["created"]),
            models.Index(fields=["-created", "-id"]),
            models.Index(fields=["uploaded_by", "-created"]),
        ]

    def __str__(self):
        return self.title or self.get_video_filename()

    def save(self, *args, **kwargs):
        if not self.title and self.video_file:
            self.title = os.path.splitext(os.path.basename(self.video_file.name))[0]
        super().save(*args, **kwargs)

    def get_video_filename(self):
        if not self.video_file:
            return ""
        return media_display_name(self.video_file)

    def get_cover_proxy_url(self):
        if not self.cover_image:
            return ""
        version = (
            int((self.updated or self.created).timestamp())
            if (self.updated or self.created)
            else self.pk
        )
        return f"{reverse('blog:video_cover_image_proxy', args=[self.pk])}?v={version}"

    def get_video_proxy_url(self):
        if not self.video_file:
            return ""
        version = (
            int((self.updated or self.created).timestamp())
            if (self.updated or self.created)
            else self.pk
        )
        return f"{reverse('blog:video_file_proxy', args=[self.pk])}?v={version}"


class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=500)
    ip_address = models.GenericIPAddressField()
    status_code = models.IntegerField(null=True, blank=True)
    response_time = models.FloatField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [models.Index(fields=["-timestamp"])]

    def __str__(self):
        return f"{self.method} {self.path} - {self.status_code}"


class Note(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notes"
    )
    title = models.CharField(max_length=50)
    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated"]
        indexes = [models.Index(fields=["user", "-updated"])]

    def __str__(self):
        return f"{self.user.username} - {self.title}"
