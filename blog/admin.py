"""
Django admin configuration for the blog application.
This module registers all models with the Django admin site and customizes
their list displays, filters, search fields, and actions.
"""

# =============================================================================
# IMPORTS
# =============================================================================

from django.contrib import admin
# admin: Django's built-in administration interface module.
# Provides the @admin.register decorator and the ModelAdmin base class.

from .models import Post, Comment, AudioPost, AuditLog
# Post: The main blog post model.
# Comment: User comments attached to posts.
# AudioPost: Audio file uploads associated with the blog.
# AuditLog: Records of HTTP requests for monitoring and debugging.


# =============================================================================
# ADMIN ACTIONS (Shared across multiple models)
# =============================================================================

def make_active(modeladmin, request, queryset):
    """
    Admin action to mark selected items as active.

    Args:
        modeladmin: The ModelAdmin instance triggering this action.
        request: The HTTP request object.
        queryset: The QuerySet of objects selected by the admin user.
    """
    queryset.update(active=True)


def make_inactive(modeladmin, request, queryset):
    """
    Admin action to mark selected items as inactive.

    Args:
        modeladmin: The ModelAdmin instance triggering this action.
        request: The HTTP request object.
        queryset: The QuerySet of objects selected by the admin user.
    """
    queryset.update(active=False)


# =============================================================================
# POST ADMIN
# =============================================================================

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Post model.
    Provides custom list display, filtering, searching, and slug auto-generation.
    """
    list_display = ["title", "slug", "author", "publish", "status"]
    # list_display: Fields shown in the admin list view for each Post instance.

    list_filter = ["status", "created", "publish", "author"]
    # list_filter: Sidebar filters for narrowing down the Post queryset.

    search_fields = ["title", "body"]
    # search_fields: Fields included in the admin search bar.

    prepopulated_fields = {"slug": ("title",)}
    # prepopulated_fields: Automatically generate slug from the title field.

    raw_id_fields = ["author"]
    # raw_id_fields: Use a search popup instead of a dropdown for the author ForeignKey.

    date_hierarchy = "publish"
    # date_hierarchy: Drill-down navigation by year, month, and day based on publish date.

    ordering = ["status", "publish"]
    # ordering: Default sort order for Post list view.

    show_facets = admin.ShowFacets.ALWAYS
    # show_facets: Display facet counts in list filters (Django 5.0+).

    class Media:
        # Media: Define extra CSS or JS files for this admin page.
        css = {"all": ("admin/css/markdownx_admin.css",)}


# =============================================================================
# COMMENT ADMIN
# =============================================================================

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Comment model.
    Provides list display with author links, filtering, and search capabilities.
    """
    list_display = ["display_name", "author", "email", "post", "created", "active"]
    # list_display: Fields shown in the admin list view for each Comment instance.

    list_filter = ["active", "created", "updated"]
    # list_filter: Sidebar filters for narrowing down the Comment queryset.

    search_fields = ["author__username", "email", "body"]
    # search_fields: Fields included in the admin search bar (supports related fields).


# =============================================================================
# AUDIO POST ADMIN
# =============================================================================

@admin.register(AudioPost)
class AudioPostAdmin(admin.ModelAdmin):
    """
    Admin configuration for the AudioPost model.
    Provides list display, filtering, search, and read-only time fields.
    """
    list_display = ["music_name", "audio_file", "description", "created", "active"]
    # list_display: Fields shown in the admin list view for each AudioPost instance.

    list_filter = ["active", "created", "updated"]
    # list_filter: Sidebar filters for narrowing down the AudioPost queryset.

    search_fields = ["music_name", "description"]
    # search_fields: Fields included in the admin search bar.

    readonly_fields = ["created", "updated"]
    # readonly_fields: Prevent editing of auto-generated timestamps.

    list_per_page = 20
    # list_per_page: Number of items shown per page in the list view.


# =============================================================================
# AUDIT LOG ADMIN
# =============================================================================

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Admin configuration for the AuditLog model.
    Displays request details, timestamps, and performance metrics.
    All fields are read-only to prevent tampering with audit records.
    """
    list_display = ["timestamp", "method", "path", "status_code", "user", "ip_address", "response_time"]
    # list_display: Fields shown in the admin list view for each AuditLog instance.

    list_filter = ["method", "status_code", "timestamp"]
    # list_filter: Sidebar filters for narrowing down the AuditLog queryset.

    search_fields = ["path", "ip_address", "user__username"]
    # search_fields: Fields included in the admin search bar.

    readonly_fields = ["user", "method", "path", "ip_address", "status_code", "response_time", "timestamp"]
    # readonly_fields: All fields are read-only to preserve audit integrity.

    list_per_page = 50
    # list_per_page: Number of items shown per page in the list view.

    date_hierarchy = "timestamp"
    # date_hierarchy: Drill-down navigation by year, month, and day based on timestamp.

# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                        blog/admin.py                                       │
# │                    (Django Admin Configuration)                            │
# └─────────────────────────────────────────────────────────────────────────────┘
#                                       │
#                                       ▼
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                            IMPORTS (Dependencies)                           │
# ├─────────────────────────────────────────────────────────────────────────────┤
# │  django.contrib           │  .models                                       │
# │  └─ admin                 │  ├─ Post                                       │
# │                           │  ├─ Comment                                    │
# │                           │  ├─ AudioPost                                  │
# │                           │  └─ AuditLog                                   │
# └─────────────────────────────────────────────────────────────────────────────┘
#                                       │
#                                       ▼
#                  ┌────────────────────────────────────────────────┐
#                  │            Admin Functions & Classes           │
#                  └────────────────────────────────────────────────┘
#                                       │
#          ┌────────────────────────────┼────────────────────────────┐
#          │                            │                            │
#          ▼                            ▼                            ▼
# ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
# │   make_active        │  │   make_inactive       │  │   PostAdmin          │
# │   (Function)         │  │   (Function)          │  │   (Class)            │
# ├──────────────────────┤  ├──────────────────────┤  ├──────────────────────┤
# │ Purpose:             │  │ Purpose:             │  │ Purpose:             │
# │   Mark selected      │  │   Mark selected      │  │   Admin interface    │
# │   items as active    │  │   items as inactive  │  │   for Post model     │
# │                      │  │                      │  │                      │
# │ Used by:             │  │ Used by:             │  │ Key Features:        │
# │   Admin actions      │  │   Admin actions      │  │   - list_display     │
# │                      │  │                      │  │   - list_filter      │
# │                      │  │                      │  │   - search_fields    │
# │                      │  │                      │  │   - prepopulated_slug│
# │                      │  │                      │  │   - raw_id_fields    │
# │                      │  │                      │  │   - date_hierarchy   │
# │                      │  │                      │  │   - show_facets      │
# └──────────────────────┘  └──────────────────────┘  └──────────────────────┘
#                                       │
#          ┌────────────────────────────┼────────────────────────────┐
#          ▼                            ▼                            ▼
# ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
# │   CommentAdmin       │  │   AudioPostAdmin      │  │   AuditLogAdmin      │
# │   (Class)            │  │   (Class)            │  │   (Class)            │
# ├──────────────────────┤  ├──────────────────────┤  ├──────────────────────┤
# │ Purpose:             │  │ Purpose:             │  │ Purpose:             │
# │   Admin interface    │  │   Admin interface    │  │   Admin interface    │
# │   for Comment model  │  │   for AudioPost model│  │   for AuditLog model │
# │                      │  │                      │  │                      │
# │ Key Features:        │  │ Key Features:        │  │ Key Features:        │
# │   - list_display     │  │   - list_display     │  │   - list_display     │
# │   - list_filter      │  │   - list_filter      │  │   - list_filter      │
# │   - search_fields    │  │   - search_fields    │  │   - search_fields    │
# │   - support for      │  │   - readonly_fields  │  │   - readonly_fields  │
# │     author relation  │  │   - list_per_page    │  │   - list_per_page    │
# │                      │  │                      │  │   - date_hierarchy   │
# └──────────────────────┘  └──────────────────────┘  └──────────────────────┘