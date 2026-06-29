# =====================
# IMPORTS
# =====================

from django.db import models
# models: Django's ORM module for defining database models
# Provides Model base class and field types (CharField, ForeignKey, etc.)

from django.utils import timezone
# timezone: Utility for handling timezone-aware datetime operations
# Used for default publication time with timezone support

from django.conf import settings
# settings: Access to Django project configuration settings
# Used to reference AUTH_USER_MODEL for ForeignKey to User

from django.urls import reverse
# reverse: Function to generate URLs by resolving view names and parameters
# Used in get_absolute_url() to create permalinks for posts

from taggit.managers import TaggableManager
# TaggableManager: Manager for handling tags on models (from django-taggit)
# Provides add(), remove(), and filtering capabilities for tags

from django.utils.text import slugify
from django.utils.html import escape

from markdownx.models import MarkdownxField

import markdown


# =====================
# CUSTOM MANAGER: PUBLISHED MANAGER
# =====================

class PublishedManager(models.Manager):
    """
    Custom model manager that filters querysets to return only published posts.

    This manager is used as `Post.published` and automatically excludes draft posts.
    It provides a clean way to get published content without repeating filter logic.

    Usage: Post.published.all() instead of Post.objects.filter(status='PB')
    """

    def get_queryset(self):
        """
        Override the base manager's get_queryset method.

        Returns only posts with status equal to PUBLISHED.
        The super().get_queryset() call gets all objects, then we filter.

        :return: QuerySet containing only published posts
        """
        return (
            super().get_queryset().filter(status=Post.Status.PUBLISHED)
        )


# =====================
# POST MODEL
# =====================

class Post(models.Model):
    """
    Blog post model representing articles written by users.

    This model stores all blog post content, metadata, and provides
    methods for URL generation and Markdown rendering.

    Features:
    - Draft/Published status with TextChoices enum
    - Automatic slug generation from title
    - Markdown support for rich content
    - Tagging capability via django-taggit
    - Publication date for scheduled publishing
    - Auto-updated timestamps for created/updated
    """

    # ----- STATUS ENUM (TextChoices) -----
    class Status(models.TextChoices):
        """
        Enum class defining possible post statuses.

        Values:
            DRAFT ('DF'): Post is not yet published (saved as 'DF' in database)
            PUBLISHED ('PB'): Post is publicly visible (saved as 'PB' in database)

        The display labels ('Draft', 'Published') appear in forms and admin.
        """
        DRAFT = 'DF', 'Draft'  # First value: DB storage, Second: Human-readable label
        PUBLISHED = 'PB', 'Published'

    # ----- BASIC FIELDS -----

    title = models.CharField(max_length=250)
    cover_image = models.ImageField(upload_to='posts/%Y/%m/%d/', blank=True, null=True)
    # CharField: Stores the post title with maximum length of 250 characters
    # Used in __str__ representation, URL slugs, and display headings

    slug = models.SlugField(
        max_length=250,
        unique_for_date='publish'
    )
    # SlugField: URL-friendly version of the title (e.g., "my-blog-post")
    # unique_for_date='publish': Slug only needs to be unique per publication date
    # Allows same slug for posts published on different dates (good for same-titled posts)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blog_posts'
    )
    # ForeignKey: Links post to a user (author)
    # settings.AUTH_USER_MODEL: Uses custom user model if defined, else defaults to User
    # on_delete=CASCADE: Delete all posts when the author user is deleted
    # related_name='blog_posts': Allows reverse access: user.blog_posts.all()

    body = MarkdownxField()
    # MarkdownxField: Enhanced TextField with Markdown support
    # Stores raw Markdown text, provides live preview in admin
    # Used with get_markdown_body() method to render to HTML

    # ----- DATE/TIME FIELDS -----

    publish = models.DateTimeField(default=timezone.now)
    # DateTimeField: When the post should be considered published
    # default=timezone.now: Auto-set to current time if not specified
    # Can be manually set to future dates for scheduled publishing
    # Used in unique_for_date constraint and URL date hierarchy

    created = models.DateTimeField(auto_now_add=True)
    # DateTimeField: When the post was first created
    # auto_now_add=True: Automatically set to current time on creation
    # Never updates after initial creation (useful for auditing)

    updated = models.DateTimeField(auto_now=True)
    # DateTimeField: When the post was last modified
    # auto_now=True: Automatically updates on every save
    # Useful for displaying "Last updated" timestamps

    status = models.CharField(
        max_length=10,
        choices=Status,
        default=Status.DRAFT
    )
    # CharField: Stores post status as short code ('DF' or 'PB')
    # choices: Limits values to those defined in Status enum
    # default=Status.DRAFT: New posts start as drafts (not immediately visible)

    # ----- TAGGING -----

    tags = TaggableManager()
    # TaggableManager: Provides tagging capabilities via django-taggit
    # Adds methods: .tags.add(), .tags.remove(), .tags.all()
    # Creates separate tag tables and many-to-many relationship
    # Allows: Post.objects.filter(tags__name='django')

    # ----- MANAGERS -----

    objects = models.Manager()
    # Default manager: Returns ALL posts (including drafts)
    # Access via: Post.objects.all()

    published = PublishedManager()

    # Custom manager: Returns ONLY published posts
    # Access via: Post.published.all()

    # ----- META CLASS -----

    class Meta:
        """
        Model metadata configuration.

        ordering: Default sort order for queries (newest first)
        indexes: Database indexes for performance optimization
        """
        ordering = ['-publish']
        # Descending order by publish date (minus sign means newest first)
        # Applied automatically when querying without explicit order_by()

        indexes = [
            models.Index(fields=['-publish']),
            # Database index on publish field (descending) for faster date-based queries
            # Improves performance for list pages that sort by publish date
        ]

        constraints = [
            models.UniqueConstraint(
                fields=['slug', 'publish'],
                name='unique_slug_per_date'
            )
        ]

    # ----- MAGIC METHODS -----

    def __str__(self):
        """
        Returns a human-readable string representation of the post.

        Used in:
        - Django admin interface (list display, dropdowns)
        - Debugging and logging
        - Shell output when printing Post objects

        :return: Post title string
        """
        return self.title

    # ----- URL METHODS -----

    def get_absolute_url(self):
        """
        Returns the canonical URL for the post detail page.

        Used by:
        - Django admin "View on site" link
        - Redirect after post creation
        - Template links: <a href="{{ post.get_absolute_url }}">

        URL pattern requires: year, month, day, and slug.
        Example URL: /blog/2024/01/15/my-post-slug/

        :return: Absolute URL path to the post detail view
        """
        return reverse(
            'blog:post_detail',
            args=[
                self.publish.year,  # 4-digit year (2024)
                self.publish.month,  # Month number (1-12)
                self.publish.day,  # Day number (1-31)
                self.slug  # URL-friendly slug
            ]
        )


    # ----- MODEL BEHAVIOR -----

    def clean(self):
        if self.pk and self.status == self.Status.PUBLISHED and not self.tags.exists():
            from django.core.exceptions import ValidationError
            raise ValidationError('发布的文章必须包含至少一个标签(tag)。')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        self.clean()
        super().save(*args, **kwargs)

    # ----- MARKDOWN RENDERING -----

    def get_markdown_body(self):
        """
        Converts Markdown body content to HTML.

        This method is called in templates to render Markdown:
            {{ post.get_markdown_body|safe }}

        The |safe filter is required because the output contains HTML tags.

        Example:
            Input: "# Hello\n\nThis is **bold** text."
            Output: '<h1>Hello</h1>\n<p>This is <strong>bold</strong> text.</p>'

        :return: HTML string converted from Markdown
        """
        return markdown.markdown(self.body)


# =====================
# COMMENT MODEL
# =====================

class Comment(models.Model):
    """
    Comment model representing user comments on blog posts.

    This model stores comment content, author information, and moderation status.
    Each comment belongs to exactly one Post (many-to-one relationship).

    Features:
    - Active flag for comment moderation (approve/hide)
    - Auto-timestamps for creation and update
    - Email field for gravatar support or reply notifications
    - Ordered by creation date (oldest first by default)
    """

    # ----- RELATIONSHIPS -----

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    # ForeignKey: Links comment to its parent post
    # on_delete=CASCADE: Delete comment when its parent post is deleted
    # related_name='comments': Allows reverse access: post.comments.all()

    # ----- AUTHOR INFORMATION -----

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blog_comments',
    )
    # ForeignKey: Links comment to the authenticated user who created it

    email = models.EmailField()
    # EmailField: Commenter's email address (for gravatar, moderation, replies)
    # Validates email format automatically
    # Not displayed publicly (typically)

    # ----- COMMENT CONTENT -----

    body = models.CharField(max_length=1000)
    # CharField: The actual comment text with 1000 character limit
    # Automatically truncated in database

    # ----- DATE/TIME FIELDS -----
    image = models.ImageField(upload_to='comments/%Y/%m/%d/', blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    # DateTimeField: When comment was first posted
    # auto_now_add=True: Set on creation, never updates
    # Used for sorting comments chronologically

    updated = models.DateTimeField(auto_now=True)
    # DateTimeField: When comment was last edited (if editing is allowed)
    # auto_now=True: Updates on every save
    # Optional feature (editing not implemented in basic version)

    # ----- MODERATION -----

    active = models.BooleanField(default=True)

    # BooleanField: Whether comment is approved and visible
    # default=True: New comments are active by default
    # Set to False for moderation queue, spam filtering, or manual approval

    # ----- META CLASS -----

    class Meta:
        """
        Model metadata configuration for Comment model.

        ordering: Show oldest comments first (chronological conversation flow)
        indexes: Database index on created field for faster date-based queries
        """
        ordering = ['created']
        # Ascending order by creation date (oldest first)
        # Natural order for discussion threads

        indexes = [
            models.Index(fields=['created']),
            # Database index on created field for faster sorting/filtering
            # Improves performance when ordering by creation date
        ]

    # ----- MAGIC METHODS -----

    def __str__(self):
        """
        Returns a human-readable string representation of the comment.

        Example output: "Comment by JohnDoe on My Blog Post"

        Used in:
        - Django admin interface
        - Debugging and logging
        - Shell output

        :return: Descriptive string with commenter name and associated post
        """
        return f"Comment by {self.display_name} on {self.post}"

    @property
    def display_name(self):
        if self.author_id:
            return self.author.username
        return self.email.split("@", 1)[0]

class AudioPost(models.Model):
    audio_file = models.FileField(upload_to='audio/%Y/%m/%d')
    description = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='audio_posts'
    )
    music_name = models.CharField(max_length=200, blank=True)
    active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created']

        indexes = [
            models.Index(fields=['created'])
        ]

    def __str__(self):
        return self.music_name or self.audio_file.name.rsplit('/', 1)[-1]

    def save(self, *args, **kwargs):
        if not self.music_name and self.audio_file:
            import os
            self.music_name = os.path.splitext(os.path.basename(self.audio_file.name))[0]
        super().save(*args, **kwargs)

# =====================
# RELATIONSHIP DIAGRAM
# =====================
#
# ┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
# │      User       │         │      Post       │         │     Comment     │
# │  (auth_user)    │         │   (blog_post)   │         │  (blog_comment) │
# ├─────────────────┤         ├─────────────────┤         ├─────────────────┤
# │ id (PK)         │◄───────│ author_id (FK)   │         │ post_id (FK)    │◄──┐
# │ username        │         │ title           │         │ name            │   │
# │ email           │         │ slug            │         │ email           │   │
# │ ...             │         │ body (Markdown) │         │ body            │   │
# └─────────────────┘         │ publish         │         │ created         │   │
#                             │ created         │         │ updated         │   │
#                             │ updated         │         │ active          │   │
#                             │ status          │         └─────────────────┘   │
#                             │ tags (M2M) ──┐  │                                │
#                             └──────────────┼──┘                                │
#                                            │                                   │
#                                    ┌───────▼───────┐                           │
#                                    │     Tag      │                           │
#                                    │ (taggit_tag) │                           │
#                                    ├───────────────┤                           │
#                                    │ id (PK)       │                           │
#                                    │ name          │                           │
#                                    │ slug          │                           │
#                                    └───────────────┘                           │
#                                                                                │
# ┌─────────────────────────────────────────────────────────────────────────────┘
# │
# └─ One-to-Many: One Post has many Comments
#    Many-to-Many: One Post has many Tags, one Tag belongs to many Posts
#    Many-to-One: One User has many Posts (one author per post)
#

# =====================
# QUERY EXAMPLES
# =====================
#
# 1. Get all published posts (using custom manager):
#    posts = Post.published.all()
#
# 2. Get all posts by a specific author:
#    posts = Post.objects.filter(author__username='john')
#
# 3. Get posts with a specific tag:
#    posts = Post.published.filter(tags__name='django')
#
# 4. Get active comments for a post:
#    comments = post.comments.filter(active=True)
#
# 5. Get all posts from the last 7 days:
#    from datetime import timedelta
#    week_ago = timezone.now() - timedelta(days=7)
#    recent = Post.published.filter(publish__gte=week_ago)
#
# 6. Count comments per post:
#    from django.db.models import Count
#    posts_with_comment_count = Post.published.annotate(
#        total_comments=Count('comments')
#    )
#
# 7. Get posts using the default manager (including drafts):
#    all_posts = Post.objects.all()
#
# 8. Get posts using published manager (excluding drafts):
#    published_posts = Post.published.all()

# =====================
# TROUBLESHOOTING
# =====================
#
# 1. MarkdownxField Import Error
#    → Ensure markdownx is installed: pip install django-markdownx
#    → Add 'markdownx' to INSTALLED_APPS in settings.py
#
# 2. TaggableManager Import Error
#    → Ensure django-taggit is installed: pip install django-taggit
#    → Add 'taggit' to INSTALLED_APPS in settings.py
#
# 3. Slug not auto-generated
#    → Check that save() method override is correct
#    → Verify slugify is imported from django.utils.text
#
# 4. unique_for_date constraint error
#    → Publish field must be a date/datetime field
#    → Identical slugs on same date will cause IntegrityError
#
# 5. Reverse accessor clashes
#    → related_name must be unique across models
#    → Using 'blog_posts' and 'comments' avoids conflicts
#
# 6. PublishedManager returning no results
#    → Check status field has value 'PB' for published posts
#    → Verify Post.Status.PUBLISHED value (should be 'PB')
#
# =====================
# AUDIT LOG MODEL
# =====================

class AuditLog(models.Model):
    """请求审计日志"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=500)
    ip_address = models.GenericIPAddressField()
    status_code = models.IntegerField(null=True, blank=True)
    response_time = models.FloatField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [models.Index(fields=['-timestamp'])]

    def __str__(self):
        return f"{self.method} {self.path} - {self.status_code}"
