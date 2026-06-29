# blog/admin.py - Django Admin Configuration for Blog Application
# ================================================================
# This module configures the Django admin interface for all models
# in the blog application, providing CRUD operations, filtering,
# searching, and custom display options for administrators.
# ================================================================


# ================================================================
# IMPORTS
# ================================================================

# Django's built-in administration interface module
# Provides AdminSite class, ModelAdmin base class, and @admin.register decorator
# The decorator registers ModelAdmin classes with the admin site
from django.contrib import admin

# format_html: Safely format HTML strings with automatic escaping
# Escapes special characters (<, >, &, ", ') to prevent XSS attacks
# Use this when inserting custom HTML into admin display columns
from django.utils.html import format_html

# Import models to be registered with the admin interface
# Each model gets its own admin configuration class
from .models import Post, Comment, AudioPost, AuditLog
# Post: Main blog post model (title, slug, body, author, status, publish dates)
# Comment: User comments on posts (name, email, body, active flag, timestamps)
# AudioPost: Audio file posts (music_name, audio_file, description, active flag)
# AuditLog: System audit log (user, action, timestamp, IP, path, response_time)


# ================================================================
# CUSTOM ADMIN ACTIONS (Example - not currently used)
# ================================================================
# These functions can be added as bulk actions in the admin list view
# They operate on a queryset of selected objects

def make_active(modeladmin, request, queryset):
    """
    Bulk action: Set selected comments to active (visible).
    Usage: Select comments in admin list, choose 'Mark selected comments as active'
    """
    queryset.update(active=True)


def make_inactive(modeladmin, request, queryset):
    """
    Bulk action: Set selected comments to inactive (hidden).
    Usage: Select comments in admin list, choose 'Mark selected comments as inactive'
    """
    queryset.update(active=False)


# ================================================================
# PostAdmin - Admin Configuration for Post Model
# ================================================================

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Post model.

    Registers Post with Django admin and customizes the interface for
    managing blog posts.

    Key Features:
    -----------------
    - List view with title, slug, author, publish date, and status columns
    - Filters for status, creation date, publication date, and author
    - Search across title and body content
    - Auto-populated slug field from title
    - Raw ID field for author selection (efficient with large user tables)
    - Date hierarchy navigation by publication date
    - Facet counts for filter options (Django 5.0+)
    - Custom MarkdownX CSS for rich text editing

    Class Attributes:
    -----------------
    list_display : tuple
        Fields shown as columns in the admin change list

    list_filter : tuple
        Fields used as filter widgets in the sidebar

    search_fields : tuple
        Fields included in the admin search box

    prepopulated_fields : dict
        Fields automatically populated from other fields (slug from title)

    raw_id_fields : tuple
        ForeignKey fields displayed as search popups (not dropdowns)

    date_hierarchy : str
        Field used for date drill-down navigation

    ordering : tuple
        Default sort order for the list view

    show_facets : admin.ShowFacets
        Controls display of facet counts in filters
    """

    # ================================================================
    # LIST VIEW CONFIGURATION
    # ================================================================
    # Controls which fields are displayed as columns in the admin
    # change list page. Each field name must exist on the model or
    # be a callable method on this ModelAdmin class.

    list_display = [
        'title',      # Post title (clickable, links to change form)
        'slug',       # URL-friendly identifier (auto-generated)
        'author',     # ForeignKey to User model (displays username)
        'publish',    # Publication date/time (DateTimeField)
        'status'      # Post status (Draft or Published)
    ]

    # ================================================================
    # FILTERS
    # ================================================================
    # Adds filter widgets to the right sidebar of the change list.
    # Users can click filter options to narrow down the queryset.

    list_filter = [
        'status',     # Filter by Draft/Published status
        'created',    # Filter by creation date (Today, Past 7 days, etc.)
        'publish',    # Filter by publication date
        'author'      # Filter by author (dropdown of all users)
    ]

    # ================================================================
    # SEARCH
    # ================================================================
    # Adds a search box above the list view.
    # Django will search across all specified fields using OR conditions.
    # Uses SQL LIKE with % wildcards for partial matching.

    search_fields = [
        'title',      # Search by post title (case-insensitive)
        'body'        # Search by post content (case-insensitive)
    ]

    # ================================================================
    # FORM FIELD PREPOPULATION
    # ================================================================
    # Automatically fills a field based on values from other fields.
    # Uses JavaScript on the admin form page.

    prepopulated_fields = {
        'slug': ('title',)    # slug = slugify(title)
        # Example: title "My Awesome Post" → slug "my-awesome-post"
    }

    # ================================================================
    # FOREIGN KEY PERFORMANCE
    # ================================================================
    # Displays ForeignKey fields as a search popup instead of a dropdown.
    # Important for performance when the related table has many rows.

    raw_id_fields = ['author']
    # Without this: Django would load ALL users into a <select> dropdown
    # With raw_id_fields: Shows an ID field with a search popup icon
    # Beneficial when User table has 1000+ records

    # ================================================================
    # DATE NAVIGATION
    # ================================================================
    # Creates drill-down navigation links for date-based filtering.
    # Displays: Year → Month → Day navigation hierarchy.

    date_hierarchy = 'publish'
    # Adds a navigation bar at the top showing:
    # 2025 ▼ → May ▼ → 15 (with clickable links)

    # ================================================================
    # DEFAULT ORDERING
    # ================================================================
    # Specifies the default ordering of objects in the change list.
    # Applied when no user sorting is active.

    ordering = ['status', 'publish']
    # Sort by status first (alphabetically: 'DF' before 'PB')
    # Then by publish date (ascending, oldest first)

    # ================================================================
    # FACET FILTERS (Django 5.0+)
    # ================================================================
    # Enables display of facet counts next to each filter option.
    # Shows how many items match each filter value.

    show_facets = admin.ShowFacets.ALWAYS
    # ALWAYS: Facet counts are always displayed
    # Other options: ShowFacets.ALLOW (configurable per filter)
    #                ShowFacets.NEVER (never display)

    # ================================================================
    # CUSTOM MEDIA
    # ================================================================
    # Specifies additional CSS and JavaScript files to include
    # in the admin change form for this model.

    class Media:
        """
        Custom CSS and JavaScript for the Post admin form.

        This class is automatically detected by Django's admin.
        The specified files are included in the admin page's <head>.

        Attributes:
            css: Dictionary mapping media types to file paths
                 Paths are relative to STATIC_URL (typically '/static/')
        """

        css = {
            'all': ('admin/css/markdownx_admin.css',)
            # 'all': Applied to all media types (screen, print, handheld)
            # markdownx_admin.css: Provides styling for MarkdownX widget
            # Enables live Markdown preview in the admin form
        }

        # Optional: JavaScript files can be added via 'js' attribute
        # js = ('admin/js/custom.js',)


# ================================================================
# CommentAdmin - Admin Configuration for Comment Model
# ================================================================

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Comment model.

    Registers Comment with Django admin and customizes the interface for
    moderating user comments on blog posts.

    Key Features:
    -----------------
    - List view with commenter details, associated post, and moderation status
    - Filters for active status, creation, and update dates
    - Search across commenter name, email, and content
    - Bulk actions can be added for moderation (make_active, make_inactive)

    Common Admin Workflow:
    -----------------------
    1. View pending comments (filter active=False)
    2. Review comment body and context
    3. Approve by setting active=True (bulk or individual)
    4. Delete spam comments
    """

    # ================================================================
    # LIST VIEW CONFIGURATION
    # ================================================================

    list_display = [
        'display_name',  # Derived comment author name
        'author',     # Linked authenticated user
        'email',      # Commenter's email (for gravatar, moderation replies)
        'post',       # Associated Post object (displays post title)
        'created',    # Submission timestamp
        'active'      # Boolean: True = visible, False = hidden/moderated
    ]

    # ================================================================
    # LIST FILTERS
    # ================================================================

    list_filter = [
        'active',     # Filter by Approved/Pending status
        'created',    # Filter by submission date
        'updated'     # Filter by last modification date
    ]
    # 'active' filter is most useful for comment moderation workflow

    # ================================================================
    # SEARCH
    # ================================================================

    search_fields = [
        'author__username',  # Search by linked username
        'email',      # Search by email address
        'body'        # Search by comment content (partial match)
    ]
    # Useful for finding comments from specific users or with keywords

    # ================================================================
    # BULK ACTIONS (Commented out in original, included for reference)
    # ================================================================
    # Uncomment to enable bulk moderation actions in the admin list view

    # actions = [make_active, make_inactive]
    # Makes 'Mark selected comments as active/inactive' available
    # in the 'Actions' dropdown above the change list


# ================================================================
# AudioPostAdmin - Admin Configuration for AudioPost Model
# ================================================================

@admin.register(AudioPost)
class AudioPostAdmin(admin.ModelAdmin):
    """
    Admin configuration for the AudioPost model.

    Registers AudioPost with Django admin and customizes the interface for
    managing audio file posts.

    Features configured:
    - List view with music_name, audio_file, description, and timestamps
    - Filters for active status and dates
    - Search across music_name and description
    - Read-only fields for created and updated timestamps
    - Pagination: 20 items per page
    """

    # ================================================================
    # LIST VIEW CONFIGURATION
    # ================================================================

    list_display = [
        'music_name',     # Track/song name
        'audio_file',     # Path to uploaded audio file
        'description',    # Track description or notes
        'created',        # Creation timestamp
        'active'          # Boolean: visible/hidden
    ]

    # ================================================================
    # LIST FILTERS
    # ================================================================

    list_filter = [
        'active',         # Filter by visible/hidden
        'created',        # Filter by creation date
        'updated'         # Filter by modification date
    ]

    # ================================================================
    # SEARCH
    # ================================================================

    search_fields = [
        'music_name',     # Search by music name (partial match)
        'description'     # Search by description (partial match)
    ]

    # ================================================================
    # READ-ONLY FIELDS
    # ================================================================
    # These fields cannot be edited in the admin form.
    # Typically used for auto-generated timestamp fields.

    readonly_fields = [
        'created',        # Auto-set on creation
        'updated'         # Auto-updated on save
    ]

    # ================================================================
    # PAGINATION
    # ================================================================

    list_per_page = 20
    # Number of items displayed per page in the change list.
    # If more than 20 items, pagination links appear at the bottom.


# ================================================================
# AuditLogAdmin - Admin Configuration for AuditLog Model
# ================================================================

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Admin configuration for the AuditLog model.

    Registers AuditLog with Django admin and customizes the interface for
    viewing system audit records.

    Key Features:
    -----------------
    - List view with timestamp, method, path, status, user, IP, and response time
    - Filters for HTTP method, status code, and timestamp
    - Search across path, IP, and username
    - All fields are read-only (audit logs should not be modified)
    - Pagination: 50 items per page
    - Date hierarchy navigation by timestamp

    Important Notes:
    ---------------
    - This is a read-only admin for security auditing
    - No add/change/delete permissions for regular admins
    - Useful for monitoring API usage and debugging
    """

    # ================================================================
    # LIST VIEW CONFIGURATION
    # ================================================================

    list_display = [
        'timestamp',      # When the request occurred
        'method',         # HTTP method (GET, POST, PUT, DELETE)
        'path',           # Request path (/api/posts/, /admin/, etc.)
        'status_code',    # HTTP status code returned (200, 404, 500, etc.)
        'user',           # Authenticated user (or None)
        'ip_address',     # Client IP address
        'response_time'   # Request duration in milliseconds
    ]

    # ================================================================
    # LIST FILTERS
    # ================================================================

    list_filter = [
        'method',         # Filter by HTTP method
        'status_code',    # Filter by response status (2xx, 4xx, 5xx)
        'timestamp'       # Filter by date/time
    ]

    # ================================================================
    # SEARCH
    # ================================================================

    search_fields = [
        'path',           # Search by URL path (partial match)
        'ip_address',     # Search by IP address
        'user__username'  # Search by related user's username (ForeignKey traversal)
    ]
    # user__username: Follows the ForeignKey to User model and searches username

    # ================================================================
    # READ-ONLY FIELDS
    # ================================================================
    # All fields are read-only because audit logs should not be
    # modified after creation. This ensures data integrity.

    readonly_fields = [
        'user',           # User who made the request
        'method',         # HTTP method
        'path',           # Request path
        'ip_address',     # Client IP
        'status_code',    # Response status
        'response_time',  # Request duration
        'timestamp'       # When the request occurred
    ]

    # ================================================================
    # PAGINATION
    # ================================================================

    list_per_page = 50
    # Show 50 audit records per page

    # ================================================================
    # DATE NAVIGATION
    # ================================================================

    date_hierarchy = 'timestamp'
    # Provides Year → Month → Day drill-down navigation
    # Very useful for auditing logs over time

    # ================================================================
    # PERMISSIONS (Optional - can be added)
    # ================================================================
    # To restrict AuditLog access to superusers only:
    #
    # def has_add_permission(self, request):
    #     return False   # No one can add audit logs manually
    #
    # def has_change_permission(self, request, obj=None):
    #     return False   # No one can edit audit logs
    #
    # def has_delete_permission(self, request, obj=None):
    #     return request.user.is_superuser   # Only superusers can delete


# ================================================================
# ADDITIONAL ADMIN FEATURES (Commented Examples for Reference)
# ================================================================

# ---- Inline Editing Example ----
#
# class CommentInline(admin.TabularInline):
#     """
#     Inline display of comments directly under the Post admin form.
#     Allows administrators to view and edit comments without leaving the post page.
#     """
#     model = Comment
#     extra = 0                 # No empty extra rows
#     fields = ['name', 'email', 'body', 'active']
#     # Display these fields in the inline table
#
# class PostAdminWithInline(admin.ModelAdmin):
#     inlines = [CommentInline]
#     # Add this to PostAdmin to show comments inline


# ---- Custom Column with HTML ----
#
# def comment_preview(self, obj):
#     """
#     Custom list_display field that shows a truncated preview of comment body.
#     Uses format_html for safe HTML rendering.
#     """
#     return format_html(
#         '<div style="max-width:300px; overflow:hidden; text-overflow:ellipsis;">{}</div>',
#         obj.body[:100]
#     )
# comment_preview.short_description = 'Comment Preview'


# ---- Fieldset Configuration ----
#
# fieldsets = (
#     ('Main Content', {
#         'fields': ('title', 'body', 'author')
#     }),
#     ('Publication', {
#         'fields': ('status', 'publish'),
#         'classes': ('collapse',)   # Collapsible section
#     }),
# )


# ================================================================
# ADMIN INTERFACE VISUALIZATION
# ================================================================
#
# Post List View (http://example.com/admin/blog/post/):
#
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │ Search: [____________________]                                              │
# ├─────────────────────────────────────────────────────────────────────────────┤
# │ Title              │ Slug               │ Author      │ Publish    │ Status│
# ├────────────────────┼────────────────────┼─────────────┼────────────┼───────┤
# │ My First Post      │ my-first-post      │ admin       │ 2025-01-15 │ Pub.  │
# │ Django Tutorial    │ django-tutorial    │ john        │ 2025-01-14 │ Draft │
# │ Python 101         │ python-101         │ jane        │ 2025-01-13 │ Pub.  │
# └────────────────────┴────────────────────┴─────────────┴────────────┴───────┘
#                      ↑
#                   list_display
#
# Filter Sidebar (with facet counts):
# ┌─────────────────────────────────────────┐
# │ Status:                                 │
# │  All (3)                               │
# │  Draft (1)                             │ ← show_facets=ALWAYS
# │  Published (2)                         │
# ├─────────────────────────────────────────┤
# │ Author:                                 │
# │  admin (2)                             │
# │  john (1)                              │
# └─────────────────────────────────────────┘


# ================================================================
# TROUBLESHOOTING COMMON ISSUES
# ================================================================
#
# 1. MarkdownX CSS Not Loading:
#    → Check that 'markdownx' is in INSTALLED_APPS
#    → Run: python manage.py collectstatic
#    → Verify the path in Media.css: 'admin/css/markdownx_admin.css'
#
# 2. raw_id_fields Not Showing Search Popup:
#    → Ensure the field is a ForeignKey
#    → Check that you have > 2 records (threshold may be 3 for dropdown)
#
# 3. prepopulated_fields Not Working:
#    → The target field must be a SlugField
#    → Check that JavaScript is enabled in browser
#    → Verify field names match exactly
#
# 4. show_facets Not Displaying Counts:
#    → Requires Django 5.0 or higher
#    → Check that 'django.contrib.admin' is in INSTALLED_APPS
#
# 5. date_hierarchy Not Appearing:
#    → Field must be DateField or DateTimeField
#    → Field name must be correct ('publish' not 'published_date')
#
# 6. Comment Admin Not Showing Email:
#    → Verify 'email' is in list_display
#    → Check that Comment model has an email field
#
# 7. AuditLog Admin Returns No Results:
#    → Ensure middleware is correctly logging to AuditLog model
#    → Check that any filters are not excluding all results
#
# 8. admin.register Not Working:
#    → Ensure the file is imported in apps.py or admin.py is imported in __init__.py
#    → Check for circular imports between models and admin
#
# 9. Media Class Not Loading CSS:
#    → Path is relative to STATIC_URL (usually /static/)
#    → Run collectstatic in production
#    → Check browser console for 404 errors

# ┌─────────────────────────────────────────────────────────────────────────────────────┐
# │                              BLOG/ADMIN.PY RELATIONSHIP DIAGRAM                    │
# └─────────────────────────────────────────────────────────────────────────────────────┘
#
# ┌─────────────────────────────────────────────────────────────────────────────────────┐
# │ 1. IMPORTS                                                                          │
# ├─────────────────────────────────────────────────────────────────────────────────────┤
# │                                                                                     │
# │  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────────────────┐  │
# │  │ django.contrib   │    │ django.utils     │    │ .models                     │  │
# │  │ .admin           │    │ .html            │    │                             │  │
# │  │                  │    │                  │    │  ┌─────────────────────────┐ │  │
# │  │  @admin.register │    │  format_html()   │    │  │  Post                   │ │  │
# │  │  admin.ModelAdmin│    │  (safe HTML      │    │  │  Comment                │ │  │
# │  │  admin.ShowFacets│    │   rendering)     │    │  │  AudioPost              │ │  │
# │  └──────────────────┘    └──────────────────┘    │  │  AuditLog               │ │  │
# │                                                   │  └─────────────────────────┘ │  │
# │                                                   └──────────────────────────────┘  │
# └─────────────────────────────────────────────────────────────────────────────────────┘
#                                        │
#                                        ▼
# ┌─────────────────────────────────────────────────────────────────────────────────────┐
# │ 2. CUSTOM ACTIONS (Utility Functions)                                               │
# ├─────────────────────────────────────────────────────────────────────────────────────┤
# │                                                                                     │
# │  ┌─────────────────────────────────────────────────────────────────────────────┐    │
# │  │  make_active(modeladmin, request, queryset)                                 │    │
# │  │  └── queryset.update(active=True)                                          │    │
# │  │                                                                             │    │
# │  │  make_inactive(modeladmin, request, queryset)                               │    │
# │  │  └── queryset.update(active=False)                                         │    │
# │  └─────────────────────────────────────────────────────────────────────────────┘    │
# │                              │                                                      │
# │                              │ (Used by CommentAdmin.actions)                      │
# │                              ▼                                                      │
# └─────────────────────────────────────────────────────────────────────────────────────┘
#                                        │
#                                        ▼
# ┌─────────────────────────────────────────────────────────────────────────────────────┐
# │ 3. MODEL ADMIN CLASSES (Registered with @admin.register)                           │
# ├─────────────────────────────────────────────────────────────────────────────────────┤
# │                                                                                     │
# │  ┌─────────────────────────────────────────────────────────────────────────────┐    │
# │  │  3a. PostAdmin (for Post model)                                              │    │
# │  │  ┌──────────────────────────────────────────────────────────────────────┐   │    │
# │  │  │  list_display      = ['title', 'slug', 'author', 'publish', 'status']│   │    │
# │  │  │  list_filter       = ['status', 'created', 'publish', 'author']      │   │    │
# │  │  │  search_fields     = ['title', 'body']                               │   │    │
# │  │  │  prepopulated_fields = {'slug': ('title',)}                          │   │    │
# │  │  │  raw_id_fields     = ['author']                                     │   │    │
# │  │  │  date_hierarchy    = 'publish'                                      │   │    │
# │  │  │  ordering          = ['status', 'publish']                          │   │    │
# │  │  │  show_facets       = admin.ShowFacets.ALWAYS                        │   │    │
# │  │  │  class Media: css = {'all': ('admin/css/markdownx_admin.css',)}     │   │    │
# │  │  └──────────────────────────────────────────────────────────────────────┘   │    │
# │  └─────────────────────────────────────────────────────────────────────────────┘    │
# │                                       │                                             │
# │  ┌─────────────────────────────────────────────────────────────────────────────┐    │
# │  │  3b. CommentAdmin (for Comment model)                                       │    │
# │  │  ┌──────────────────────────────────────────────────────────────────────┐   │    │
# │  │  │  list_display  = ['name', 'email', 'post', 'created', 'active']     │   │    │
# │  │  │  list_filter   = ['active', 'created', 'updated']                   │   │    │
# │  │  │  search_fields = ['name', 'email', 'body']                          │   │    │
# │  │  │  actions       = [make_active, make_inactive] (commented)           │   │    │
# │  │  └──────────────────────────────────────────────────────────────────────┘   │    │
# │  └─────────────────────────────────────────────────────────────────────────────┘    │
# │                                       │                                             │
# │  ┌─────────────────────────────────────────────────────────────────────────────┐    │
# │  │  3c. AudioPostAdmin (for AudioPost model)                                   │    │
# │  │  ┌──────────────────────────────────────────────────────────────────────┐   │    │
# │  │  │  list_display    = ['music_name', 'audio_file', 'description',      │   │    │
# │  │  │                     'created', 'active']                             │   │    │
# │  │  │  list_filter     = ['active', 'created', 'updated']                 │   │    │
# │  │  │  search_fields   = ['music_name', 'description']                    │   │    │
# │  │  │  readonly_fields = ['created', 'updated']                           │   │    │
# │  │  │  list_per_page   = 20                                               │   │    │
# │  │  └──────────────────────────────────────────────────────────────────────┘   │    │
# │  └─────────────────────────────────────────────────────────────────────────────┘    │
# │                                       │                                             │
# │  ┌─────────────────────────────────────────────────────────────────────────────┐    │
# │  │  3d. AuditLogAdmin (for AuditLog model)                                     │    │
# │  │  ┌──────────────────────────────────────────────────────────────────────┐   │    │
# │  │  │  list_display    = ['timestamp', 'method', 'path', 'status_code',   │   │    │
# │  │  │                     'user', 'ip_address', 'response_time']           │   │    │
# │  │  │  list_filter     = ['method', 'status_code', 'timestamp']           │   │    │
# │  │  │  search_fields   = ['path', 'ip_address', 'user__username']         │   │    │
# │  │  │  readonly_fields = [ALL FIELDS]  (all fields read-only)             │   │    │
# │  │  │  list_per_page   = 50                                               │   │    │
# │  │  │  date_hierarchy  = 'timestamp'                                      │   │    │
# │  │  └──────────────────────────────────────────────────────────────────────┘   │    │
# │  └─────────────────────────────────────────────────────────────────────────────┘    │
# └─────────────────────────────────────────────────────────────────────────────────────┘
#                                        │
#                                        ▼
# ┌─────────────────────────────────────────────────────────────────────────────────────┐
# │ 4. DEPENDENCY FLOW                                                                  │
# ├─────────────────────────────────────────────────────────────────────────────────────┤
# │                                                                                     │
# │  ┌─────────────────────────────────────────────────────────────────────────────┐    │
# │  │                        DJANGO ADMIN SITE                                     │    │
# │  │  (django.contrib.admin.sites.AdminSite)                                     │    │
# │  └─────────────────────────────────────────────────────────────────────────────┘    │
# │                              │           │           │           │                   │
# │                              ▼           ▼           ▼           ▼                   │
# │  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐│
# │  │   PostAdmin      │ │  CommentAdmin    │ │  AudioPostAdmin  │ │  AuditLogAdmin   ││
# │  │  @admin.register │ │ @admin.register  │ │ @admin.register  │ │ @admin.register  ││
# │  └────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘│
# │           │                    │                    │                    │         │
# │           ▼                    ▼                    ▼                    ▼         │
# │  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐│
# │  │   Post Model     │ │  Comment Model   │ │  AudioPost Model │ │  AuditLog Model  ││
# │  │  (.models.Post)  │ │ (.models.Comment)│ │(.models.AudioPost)│ │(.models.AuditLog)││
# │  └──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘│
# └─────────────────────────────────────────────────────────────────────────────────────┘
#                                        │
#                                        ▼
# ┌─────────────────────────────────────────────────────────────────────────────────────┐
# │ 5. ADMIN URL HIERARCHY                                                              │
# ├─────────────────────────────────────────────────────────────────────────────────────┤
# │                                                                                     │
# │  /admin/                                                                            │
# │    ├── blog/                                                                        │
# │    │   ├── post/          → PostAdmin                                              │
# │    │   │   ├── [list]     → list_display: title, slug, author, publish, status    │
# │    │   │   ├── [filter]   → status, created, publish, author                      │
# │    │   │   ├── [search]   → title, body                                          │
# │    │   │   ├── [add]      → prepopulated_fields: slug from title                  │
# │    │   │   └── [change]   → raw_id_fields: author, Media: markdownx CSS          │
# │    │   ├── comment/        → CommentAdmin                                         │
# │    │   │   ├── [list]     → list_display: name, email, post, created, active     │
# │    │   │   ├── [filter]   → active, created, updated                             │
# │    │   │   └── [search]   → name, email, body                                   │
# │    │   ├── audiopost/      → AudioPostAdmin                                      │
# │    │   │   ├── [list]     → music_name, audio_file, description, created, active │
# │    │   │   ├── [filter]   → active, created, updated                             │
# │    │   │   └── [search]   → music_name, description                              │
# │    │   └── auditlog/       → AuditLogAdmin                                       │
# │    │       ├── [list]     → timestamp, method, path, status_code, user, ip, rt   │
# │    │       ├── [filter]   → method, status_code, timestamp                       │
# │    │       └── [search]   → path, ip_address, user__username                     │
# └─────────────────────────────────────────────────────────────────────────────────────┘
#                                        │
#                                        ▼
# ┌─────────────────────────────────────────────────────────────────────────────────────┐
# │ 6. FEATURE SUMMARY TABLE                                                            │
# ├─────────────────────────────────────────────────────────────────────────────────────┤
# │                                                                                     │
# │  ┌────────────────┬────────────┬────────────┬────────────┬────────────┐            │
# │  │    Feature     │  PostAdmin │CommentAdmin│AudioPost   │AuditLog    │            │
# │  │                │            │            │ Admin      │Admin       │            │
# │  ├────────────────┼────────────┼────────────┼────────────┼────────────┤            │
# │  │ list_display   │   5 cols   │   5 cols   │   5 cols   │   7 cols   │            │
# │  │ list_filter    │   4        │   3        │   3        │   3        │            │
# │  │ search_fields  │   2        │   3        │   2        │   3        │            │
# │  │ prepopulated   │   slug     │   -        │   -        │   -        │            │
# │  │ raw_id_fields  │   author   │   -        │   -        │   -        │            │
# │  │ readonly_fields│   -        │   -        │ created,   │ ALL FIELDS │            │
# │  │                │            │            │ updated    │            │            │
# │  │ date_hierarchy │   publish  │   -        │   -        │ timestamp  │            │
# │  │ list_per_page  │   default  │   default  │   20       │   50       │            │
# │  │ show_facets    │   ALWAYS   │   default  │   default  │   default  │            │
# │  │ custom Media   │   CSS      │   -        │   -        │   -        │            │
# │  └────────────────┴────────────┴────────────┴────────────┴────────────┘            │
# └─────────────────────────────────────────────────────────────────────────────────────┘
