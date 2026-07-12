"""
Data models for the blog application.

This module defines all database models including Blog Posts, Comments,
Audio Posts, and Audit Logs. It also includes custom model managers,
validation logic, and relationship definitions.
"""

from itertools import count

# =============================================================================
# IMPORTS (All imports moved to the top)
# =============================================================================

import os
# os: Provides operating system interfaces, used for file path manipulation.

import markdown
# markdown: Converts Markdown text to HTML for rendering post bodies.

from django.conf import settings
# settings: Accesses Django project settings, used for AUTH_USER_MODEL.

from django.db import models
# models: Django's ORM module. Provides Model, Manager, and field types.

from django.urls import reverse
# reverse: Generates URLs from named URL patterns.

from django.utils import timezone
# timezone: Timezone-aware datetime utilities.

from django.utils.text import slugify
# slugify: Converts a string to a URL-friendly slug.

from django.core.exceptions import ValidationError
# ValidationError: Exception for data validation failures.

from markdownx.models import MarkdownxField
# MarkdownxField: A custom model field that stores Markdown content.

from taggit.managers import TaggableManager
# TaggableManager: Manages many-to-many relationships with tags.


# =============================================================================
# CUSTOM MANAGER
# =============================================================================

class PublishedManager(models.Manager):
    """
    Custom model manager that filters querysets to return only published posts.
    """

    def get_queryset(self):
        """
        Override the default queryset to filter by PUBLISHED status.

        Returns:
            QuerySet: A queryset containing only posts with status='PB'.
        """
        return super().get_queryset().filter(status=Post.Status.PUBLISHED)


# =============================================================================
# POST MODEL
# =============================================================================

class Post(models.Model):
    """
    Blog post model representing articles written by users.

    Features:
        - Draft/Published status management
        - Automatic slug generation
        - Markdown content support
        - Tagging via django-taggit
        - Publication date hierarchy
        - Custom manager for published posts only
    """

    class Status(models.TextChoices):
        """Enum defining possible post statuses."""
        DRAFT = "DF", "Draft"
        PUBLISHED = "PB", "Published"

    # Core fields
    title = models.CharField(max_length=250)
    cover_image = models.ImageField(upload_to="posts/%Y/%m/%d/", blank=True, null=True)
    slug = models.SlugField(max_length=250, unique_for_date="publish")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blog_posts")
    body = MarkdownxField()

    # Time fields
    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # Status and tags
    status = models.CharField(max_length=10, choices=Status, default=Status.DRAFT)
    tags = TaggableManager()

    # Managers
    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        ordering = ["-publish"]
        indexes = [models.Index(fields=["-publish"])]
        constraints = [models.UniqueConstraint(fields=["slug", "publish"], name="unique_slug_per_date")]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("blog:post_detail", args=[self.publish.year, self.publish.month, self.publish.day, self.slug])

    def build_slug(self):
        base_slug = slugify(self.title)
        if not base_slug:
            timestamp = timezone.localtime(self.publish or timezone.now()).strftime('%Y%m%d%H%M%S')
            base_slug = f'post-{timestamp}'

        base_slug = base_slug[:250]
        publish_date = timezone.localtime(self.publish or timezone.now()).date()
        existing = Post.objects.filter(publish__date=publish_date)
        if self.pk:
            existing = existing.exclude(pk=self.pk)

        for index in count(1):
            suffix = '' if index == 1 else f'-{index}'
            candidate = f'{base_slug[:250 - len(suffix)]}{suffix}'
            if candidate and not existing.filter(slug=candidate).exists():
                return candidate

        raise ValueError('Unable to generate a unique slug for the post.')

    def clean(self):
        if self.pk and self.status == self.Status.PUBLISHED and not self.tags.exists():
            raise ValidationError("发布的文章必须包含至少一个标签(tag)。")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.build_slug()
        self.clean()
        super().save(*args, **kwargs)

    def get_markdown_body(self):
        return markdown.markdown(self.body)

    def get_cover_image_proxy_url(self):
        if not self.cover_image:
            return ""
        return reverse("blog:post_cover_image", args=[self.pk])


# =============================================================================
# COMMENT MODEL
# =============================================================================

class Comment(models.Model):
    """
    Comment model representing user comments on blog posts.

    Features:
        - Links to parent Post and author User
        - Email storage for Gravatar or notifications
        - Active flag for moderation
        - Optional image upload
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blog_comments")
    email = models.EmailField()
    body = models.CharField(max_length=1000)
    image = models.ImageField(upload_to="comments/%Y/%m/%d/", blank=True, null=True)
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
        return f"Comment by {self.display_name} on {self.post}: {preview}" if preview else f"Comment by {self.display_name} on {self.post}"

    @property
    def display_name(self):
        if self.author_id:
            return self.author.username
        return self.email.split("@", 1)[0]

    def get_image_proxy_url(self):
        if not self.image:
            return ""
        return reverse("blog:comment_image", args=[self.pk])


# =============================================================================
# AUDIO POST MODEL
# =============================================================================

class AudioPost(models.Model):
    """
    Audio post model for uploading and managing audio files.

    Features:
        - File upload with date-based folder structure
        - Auto-generated music name from filename
        - Active/inactive state management
        - Automatic timestamp tracking
    """
    audio_file = models.FileField(upload_to="audio/%Y/%m/%d")
    cover_image = models.ImageField(upload_to="audio/covers/%Y/%m/%d", blank=True, null=True)
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="audio_posts")
    music_name = models.CharField(max_length=200, blank=True)
    active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]
        indexes = [models.Index(fields=["created"])]

    def __str__(self):
        return self.music_name or self.audio_file.name.rsplit("/", 1)[-1]

    def save(self, *args, **kwargs):
        if not self.music_name and self.audio_file:
            self.music_name = os.path.splitext(os.path.basename(self.audio_file.name))[0]
        super().save(*args, **kwargs)

    def get_audio_filename(self):
        if not self.audio_file:
            return ""
        return self.audio_file.name.rsplit("/", 1)[-1]

    def get_cover_filename(self):
        if not self.cover_image:
            return ""
        return self.cover_image.name.rsplit("/", 1)[-1]

    def get_audio_proxy_url(self):
        if not self.audio_file:
            return ""
        version = int((self.updated or self.created).timestamp()) if (self.updated or self.created) else self.pk
        return f'{reverse("blog:audio_file_proxy", args=[self.pk])}?v={version}'

    def get_cover_image_proxy_url(self):
        if not self.cover_image:
            return ""
        version = int((self.updated or self.created).timestamp()) if (self.updated or self.created) else self.pk
        return f'{reverse("blog:audio_cover_image_proxy", args=[self.pk])}?v={version}'



class VideoPost(models.Model):
    video_file = models.FileField(upload_to="videos/%Y/%m/%d")
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="video_posts")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]
        indexes = [models.Index(fields=["created"])]

    def __str__(self):
        return self.title or self.get_video_filename()

    def save(self, *args, **kwargs):
        if not self.title and self.video_file:
            self.title = os.path.splitext(os.path.basename(self.video_file.name))[0]
        super().save(*args, **kwargs)

    def get_video_filename(self):
        if not self.video_file:
            return ""
        return self.video_file.name.rsplit("/", 1)[-1]

    def get_video_proxy_url(self):
        if not self.video_file:
            return ""
        version = int((self.updated or self.created).timestamp()) if (self.updated or self.created) else self.pk
        return f'{reverse("blog:video_file_proxy", args=[self.pk])}?v={version}'


# =============================================================================
# AUDIT LOG MODEL
# =============================================================================

class AuditLog(models.Model):
    """
    Audit log model for recording HTTP requests and responses.

    Features:
        - Stores request method, path, and response status
        - Tracks user, IP address, and response time
        - Read-only historical records for security monitoring
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
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

# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                         blog/models.py                                     │
# │                     (Database Models Definition)                           │
# └─────────────────────────────────────────────────────────────────────────────┘
#                                       │
#                                       ▼
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                            IMPORTS (Dependencies)                           │
# ├─────────────────────────────────────────────────────────────────────────────┤
# │  os               │  django.db.models        │  django.urls                │
# │  markdown         │  ├─ Model                │  └─ reverse                 │
# │  django.conf      │  ├─ Manager              │  django.utils               │
# │  └─ settings      │  ├─ ForeignKey           │  ├─ timezone                │
# │  django.core      │  ├─ CharField            │  └─ text.slugify            │
# │  └─ exceptions    │  ├─ DateTimeField        │  markdownx.models           │
# │      └─ Validation│  ├─ ImageField           │  └─ MarkdownxField          │
# │          Error     │  ├─ SlugField            │  taggit.managers            │
# │                    │  ├─ TextChoices          │  └─ TaggableManager         │
# │                    │  ├─ BooleanField         │                             │
# │                    │  ├─ EmailField           │                             │
# │                    │  └─ GenericIPAddressField │                             │
# └─────────────────────────────────────────────────────────────────────────────┘
#                                       │
#                                       ▼
#                  ┌────────────────────────────────────────────────┐
#                  │         Models, Managers & Classes             │
#                  └────────────────────────────────────────────────┘
#                                       │
#          ┌────────────────────────────┼────────────────────────────┐
#          ▼                            ▼                            ▼
# ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
# │   PublishedManager   │  │   Post               │  │   Comment            │
# │   (Class)            │  │   (Model)            │  │   (Model)            │
# ├──────────────────────┤  ├──────────────────────┤  ├──────────────────────┤
# │ Inherits:            │  │ Status Choices:      │  │ Fields:              │
# │   models.Manager     │  │   DRAFT, PUBLISHED   │  │   post               │
# │                      │  │                      │  │   author             │
# │ Purpose:             │  │ Custom Methods:      │  │   email              │
# │   Return only        │  │   get_absolute_url() │  │   body               │
# │   published posts    │  │   get_markdown_body()│  │   image              │
# │                      │  │   clean()            │  │   created            │
# │ Methods:             │  │   save()             │  │   updated            │
# │   get_queryset()     │  │                      │  │   active             │
# │                      │  │ Meta:                │  │                      │
# │                      │  │   ordering           │  │ Meta:                │
# │                      │  │   indexes            │  │   ordering           │
# │                      │  │   constraints        │  │   indexes            │
# └──────────────────────┘  └──────────────────────┘  └──────────────────────┘
#                                       │
#          ┌────────────────────────────┼────────────────────────────┐
#          ▼                            ▼                            ▼
# ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
# │   AudioPost          │  │   AuditLog           │  │                      │
# │   (Model)            │  │   (Model)            │  │                      │
# ├──────────────────────┤  ├──────────────────────┤  │                      │
# │ Fields:              │  │ Fields:              │  │                      │
# │   audio_file         │  │   user               │  │                      │
# │   description        │  │   method             │  │                      │
# │   uploaded_by        │  │   path               │  │                      │
# │   music_name         │  │   ip_address         │  │                      │
# │   active             │  │   status_code        │  │                      │
# │   created            │  │   response_time      │  │                      │
# │   updated            │  │   timestamp          │  │                      │
# │                      │  │                      │  │                      │
# │ Meta:                │  │ Meta:                │  │                      │
# │   ordering           │  │   ordering           │  │                      │
# │   indexes            │  │   indexes            │  │                      │
# │                      │  │                      │  │                      │
# │ Custom Method:       │  │                      │  │                      │
# │   save() auto-       │  │                      │  │                      │
# │   generate music_name│  │                      │  │                      │
# └──────────────────────┘  └──────────────────────┘  └──────────────────────┘
