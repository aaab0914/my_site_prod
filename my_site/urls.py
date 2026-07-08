# ========================================
# IMPORTS
# ========================================

from django.contrib import admin
# Django's built-in administration module
# Provides the admin interface at /admin/

from django.urls import path, include
# path: Function for defining URL patterns
# Example: path('admin/', admin.site.urls)
# include: Function for including other URL configurations
# Example: include('blog.urls', namespace='blog')

from django.contrib.sitemaps.views import sitemap
# sitemap: View function for generating sitemap XML
# Used for SEO (Search Engine Optimization)
# Generates /sitemap.xml with all public URLs

from markdownx import urls as markdownx_urls
# markdownx_urls: URL patterns for django-markdownx
# Provides routes for Markdown live preview functionality
# For example: /markdownx/upload/ for image uploads

from blog.sitemaps import PostSitemap
from .metrics import metrics_view
# PostSitemap: Sitemap class for Post model (defined in blog/sitemaps.py)
# Tells Django which posts to include in the sitemap

from django.conf.urls.static import static
# static: Helper function to serve media files in development
# Used when DEBUG=True to serve uploaded files

from django.conf import settings
from django.views.generic import TemplateView
# settings: Django project configuration settings
# Used to access MEDIA_URL and MEDIA_ROOT


# ========================================
# SITEMAP CONFIGURATION
# ========================================

sitemaps = {
    'posts': PostSitemap,
}
# Dictionary mapping sitemap names to sitemap classes
# 'posts' will appear in the sitemap as /sitemap.xml?section=posts
# This tells Django which models to include in the sitemap


# ========================================
# URL PATTERNS
# ========================================

urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html"), name="site_index"),
    # ===== ADMIN INTERFACE =====
    # Django Admin dashboard for managing models
    # Accessible at: http://localhost:8001/admin/
    path("admin/", admin.site.urls),

    # ===== BLOG APPLICATION =====
    # All blog-related URLs (posts, comments, tags, etc.)
    # Defined in blog/urls.py with namespace='blog'
    # Example: /blog/posts/, /blog/2024/01/15/my-post/
    path('blog/', include('blog.urls', namespace='blog')),

    # ===== SITEMAP =====
    # XML sitemap for search engine crawlers
    # Helps Google and other search engines index all posts
    # Accessible at: http://localhost:8001/sitemap.xml
    path(
        'sitemap.xml',
        sitemap,
        {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemaps'
    ),

    # ===== MARKDOWNX =====
    # URL patterns for django-markdownx library
    # Provides live preview and image upload functionality
    # Accessible at: /markdownx/upload/ for image uploads
    path('markdownx/', include(markdownx_urls)),

    # ===== USERS APPLICATION =====
    # All user-related URLs (registration, login, profile, etc.)
    # Defined in users/urls.py with namespace='users'
    # Example: /users/register/, /users/login/, /users/profile/
    path('users/', include('users.urls', namespace='users')),
    path("metrics", metrics_view, name="metrics"),
]

# ===== MEDIA FILES (DEVELOPMENT ONLY) =====
# Serve user-uploaded files (images, avatars, etc.) during development
# This is only active when DEBUG=True in settings.py
# In production, media files should be served by nginx or a CDN
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# ========================================
# ADDITIONAL INFORMATION
# ========================================

# URL Hierarchy:
# ┌─────────────────────────────────────────────┐
# │ http://localhost:8001/ (Base URL)           │
# │   │                                         │
# │   ├─ admin/        → Django Admin           │
# │   ├─ blog/         → Blog app (posts)       │
# │   │   ├─ all/      → All posts list         │
# │   │   ├─ create/   → Create new post        │
# │   │   ├─ search/   → Search posts           │
# │   │   ├─ tag/      → Tag filtering          │
# │   │   └─ feed/     → RSS feed               │
# │   ├─ sitemap.xml   → XML Sitemap            │
# │   ├─ markdownx/    → Markdown live preview  │
# │   └─ users/        → User management        │
# │       ├─ register/ → User registration      │
# │       ├─ login/    → User login             │
# │       ├─ profile/  → User profile           │
# │       └─ logout/   → User logout            │
# └─────────────────────────────────────────────┘
