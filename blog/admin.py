# blog/admin.py
# ========================================
# Imports
# ========================================

from django.contrib import admin
# admin: Django's built-in administration interface module
# Provides the AdminSite class, ModelAdmin base class, and registration decorator

from django.utils.html import format_html
# format_html: Utility for safely formatting HTML strings
# Escapes special characters to prevent XSS attacks
# Use when inserting custom HTML into admin display

from .models import Post, Comment


# Post: The main blog post model (with draft/published status, slug, author, etc.)
# Comment: The comment model (with name, email, body, active flag, etc.)


# ========================================
# Admin Configuration for Post
# ========================================

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Post model.

    This class customizes how Post objects are displayed, filtered, searched,
    and edited in the Django admin interface.

    The @admin.register decorator automatically registers this admin class
    with the Django admin site for the Post model.

    Features configured:
    - List view columns and filters
    - Search functionality
    - Auto-populated slug field
    - Author selection via raw_id_fields (efficient for many users)
    - Date hierarchy navigation
    - Facet counts for better filtering UX
    - Custom CSS for MarkdownX widget
    """

    # ----- LIST VIEW CONFIGURATION -----
    # Controls which fields are displayed in the admin change list page

    list_display = [
        'title',  # Post title (clickable by default)
        'slug',  # URL-friendly identifier
        'author',  # User who wrote the post (ForeignKey)
        'publish',  # Publication date/time
        'status'  # Draft or Published (from Status enum)
    ]
    # These columns appear as table headers in the admin list view

    # ----- FILTERS -----
    # Adds filter widgets to the right sidebar for quick filtering

    list_filter = [
        'status',  # Filter by Draft/Published status
        'created',  # Filter by creation date (Today, Past 7 days, This month, etc.)
        'publish',  # Filter by publication date
        'author'  # Filter by author (requires select widget)
    ]
    # Users can click filter options to narrow down the list

    # ----- SEARCH -----
    # Adds a search box to search across specified fields

    search_fields = [
        'title',  # Search by post title (partial match, case-insensitive)
        'body'  # Search by post content (partial match, case-insensitive)
    ]
    # Search queries use SQL LIKE (contains) for these fields

    # ----- FORM FIELD PREPOPULATION -----

    prepopulated_fields = {
        'slug': ('title',)  # Auto-generate slug from title field when typing
    }
    # When user types a title, slug field is automatically filled
    # Example: title "My Blog Post" → slug "my-blog-post"
    # Uses JavaScript in the admin form

    # ----- FOREIGN KEY PERFORMANCE -----

    raw_id_fields = ['author']
    # Displays a search popup instead of a dropdown for selecting author
    # Benefits:
    #   - Efficient for large user tables (thousands of users)
    #   - Avoids loading all users into a dropdown
    #   - Provides search functionality for author selection
    # Without this, the admin would generate a <select> with all User objects

    # ----- DATE NAVIGATION -----

    date_hierarchy = 'publish'
    # Creates a drill-down navigation bar for date filtering
    # Shows: Year → Month → Day navigation links
    # Example: 2025 ▼ → May ▼ → 15
    # Only works with DateField or DateTimeField

    # ----- DEFAULT ORDERING -----

    ordering = ['status', 'publish']
    # Default sort order for posts in admin list view
    # First sorts by status (DF before PB, alphabetically)
    # Then sorts by publish date (ascending, oldest first)
    # Note: Ascending by status shows Drafts first, then Published

    # ----- FACET FILTERS (Django 5.0+ feature) -----

    show_facets = admin.ShowFacets.ALWAYS

    # Enables facet counts for applied filters in the admin object list
    # Shows how many items match each filter option
    # Example: "Status: Draft (3) | Published (12)"
    # ALWAYS means facet counts are always displayed
    # Other options: ALLOW (configurable per filter), NEVER

    # ----- CUSTOM MEDIA (CSS/JS) -----

    class Media:
        """
        Custom CSS and JavaScript for the admin interface.

        This class is automatically detected by Django and the media files
        are included in the admin change form for Post.
        """

        # CSS files to include in the admin page for this model
        css = {
            'all': ('admin/css/markdownx_admin.css',)
            # 'all': Applied to all media types (screen, print, etc.)
            # Path is relative to STATIC_URL (typically /static/)
            # markdownx_admin.css provides styling for MarkdownX widget
            # This enables the live Markdown preview in admin
        }

        # Optional: Can also include JS files
        # js = ('admin/js/custom.js',)


# ========================================
# Admin Configuration for Comment
# ========================================

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Comment model.

    This class customizes how Comment objects are displayed and managed
    in the Django admin interface.

    The @admin.register decorator automatically registers this admin class
    with the Django admin site for the Comment model.

    Features configured:
    - List view columns (with moderation actions)
    - Filter by active status and dates
    - Search by author name, email, and content
    - Custom actions can be added for bulk moderation
    """

    # ----- LIST VIEW CONFIGURATION -----
    # Controls which fields are displayed in the admin change list page

    list_display = [
        'name',  # Commenter's name (displayed with the comment)
        'email',  # Commenter's email (for gravatar or moderation/replies)
        'post',  # Parent post this comment belongs to (ForeignKey)
        'created',  # When the comment was submitted
        'active'  # Boolean: whether comment is visible (True) or hidden (False)
    ]
    # For moderate comments, you typically want to see 'active' to approve/hide

    # ----- LIST FILTERS -----
    # Adds filter widgets to the right sidebar

    list_filter = [
        'active',  # Filter by Active/Inactive (approved vs pending)
        'created',  # Filter by creation date
        'updated'  # Filter by last modification date
    ]
    # Most important filter: 'active' for moderation workflow
    # Allows quick filtering of unapproved comments

    # ----- SEARCH FIELDS -----

    search_fields = [
        'name',  # Search by commenter name (partial match)
        'email',  # Search by email address
        'body'  # Search by comment content (partial match)
    ]
    # Useful for finding comments by specific users or containing certain keywords

# ========================================
# Extended Configuration Options (Not in original, but useful to know)
# ========================================
#
# 1. Custom Actions for Bulk Operations:
#
#    @admin.action(description="Mark selected comments as active")
#    def make_active(modeladmin, request, queryset):
#        queryset.update(active=True)
#
#    @admin.action(description="Mark selected comments as inactive")
#    def make_inactive(modeladmin, request, queryset):
#        queryset.update(active=False)
#
#    class CommentAdmin(admin.ModelAdmin):
#        actions = [make_active, make_inactive]
#
# 2. Customizing the Detail Form:
#
#    fieldsets = (
#        ('Comment Information', {
#            'fields': ('name', 'email', 'post', 'body')
#        }),
#        ('Moderation', {
#            'fields': ('active',),
#            'classes': ('collapse',)  # Collapsible section
#        }),
#    )
#
# 3. Read-only Fields:
#
#    readonly_fields = ['created', 'updated']
#
# 4. Inline Editing of Related Objects:
#
#    class CommentInline(admin.TabularInline):
#        model = Comment
#        extra = 0
#        fields = ['name', 'email', 'body', 'active']
#
#    class PostAdmin(admin.ModelAdmin):
#        inlines = [CommentInline]
#
# 5. Custom Column with HTML:
#
#    def comment_preview(self, obj):
#        return format_html('<div style="max-width:300px">{}</div>', obj.body[:100])
#    comment_preview.short_description = 'Preview'


# ========================================
# ADMIN INTERFACE VISUALIZATION
# ========================================
#
# Post List View (/admin/blog/post/):
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │ Search: [____________________]                                              │
# ├─────────────────────────────────────────────────────────────────────────────┤
# │ Title              │ Slug               │ Author      │ Publish    │ Status│
# ├────────────────────┼────────────────────┼─────────────┼────────────┼───────┤
# │ My First Post      │ my-first-post      │ admin       │ 2025-01-15 │ Pub.  │
# │ Django Tutorial    │ django-tutorial    │ john        │ 2025-01-14 │ Draft │
# └────────────────────┴────────────────────┴─────────────┴────────────┴───────┘
#                                      ↑
#                                   list_display
#
# Filter Sidebar:
# ┌─────────────────────────┐
# │ Status:                 │
# │  All (3)                │
# │  Draft (1)              │
# │  Published (2)          │ <- show_facets enabled
# ├─────────────────────────┤
# │ Created:                │
# │  Any date               │
# │  Today (0)              │
# │  Past 7 days (1)        │
# └─────────────────────────┘


# ========================================
# TROUBLESHOOTING
# ========================================
#
# 1. MarkdownX CSS not loading
#    → Check that 'markdownx' is in INSTALLED_APPS
#    → Run: python manage.py collectstatic
#    → Verify markdownx_admin.css exists in static files
#
# 2. raw_id_fields not showing search widget
#    → Ensure the field is a ForeignKey (raw_id_fields only works with FKs)
#    → Check that you have at least 2 users (dropdown vs popup threshold)
#
# 3. prepopulated_fields not working
#    → The dependent field must be a SlugField
#    → Check that JavaScript is enabled in browser
#    → Verify the field names match exactly
#
# 4. show_facets not showing counts
#    → Requires Django 5.0 or higher
#    → Check that 'django.contrib.admin' is in INSTALLED_APPS
#
# 5. date_hierarchy not appearing
#    → Field must be DateField or DateTimeField
#    → Field name must be correct ('publish' not 'published_date')
#
# 6. Media class not loading CSS
#    → Path is relative to STATIC_URL
#    → Run collectstatic in production
#    → Check browser console for 404 errors
#
# 7. Comment admin not showing email field
#    → Verify 'email' is in list_display
#    → Check that Comment model has an email field
#
# 8. list_display showing __str__ instead of custom fields
#    → Ensure field names are spelled correctly
#    → For ForeignKey, use 'author__username' style for related fields