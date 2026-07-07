# blog/apps.py

# =====================
# IMPORTS
# =====================

from django.apps import AppConfig
import logging


logger = logging.getLogger(__name__)


# connection: Django's database connection wrapper
# Used to execute raw SQL queries for connection testing


# =====================
# BLOG APPLICATION CONFIGURATION
# =====================

class BlogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog'

    def ready(self):
        try:
            from . import signals
        except ImportError as exc:
            logger.warning("Failed to import blog signals: %s", exc)
        try:
            import my_site.media_signals
        except ImportError as exc:
            logger.warning("Failed to import media signals: %s", exc)

# =====================
# SIGNAL MODULE EXAMPLE (signals.py)
# =====================
#
# If you create a signals.py file, typical content might be:
#
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import Post
#
# @receiver(post_save, sender=Post)
# def post_saved_handler(sender, instance, created, **kwargs):
#     """Handle post-save events (e.g., send notifications, update caches)"""
#     if created:
#         print(f"New post created: {instance.title}")
#     else:
#         print(f"Post updated: {instance.title}")


# =====================
# NOTES ON APP CONFIG REGISTRATION
# =====================
#
# Method 1: Default (implicit) registration - Django auto-detects subclasses
#   INSTALLED_APPS = ['blog']  # Django finds BlogConfig automatically
#
# Method 2: Explicit registration (recommended for clarity)
#   INSTALLED_APPS = ['blog.apps.BlogConfig', ...]
#
# The explicit method is preferred because it clearly shows which config class
# Django should use, especially if you have custom ready() logic.
#
# To use explicit registration, change settings.py:
#   INSTALLED_APPS = [
#       'blog.apps.BlogConfig',  # Explicit
#       # 'blog',                 # Implicit (not needed if using explicit)
#   ]


# =====================
# READY() METHOD BEST PRACTICES
# =====================
#
# 1. Keep it Idempotent:
#    - Should be safe to call multiple times
#    - Django calls ready() only once, but tests may cause multiple calls
#
# 2. Avoid Circular Imports:
#    - Use local imports inside ready() (like `from . import signals`)
#    - Don't import models at module level if used in ready()
#
# 3. Handle Errors Gracefully:
#    - Use try/except for external dependencies
#    - Use logging instead of print() in production
#
# Example with logging:
#   import logging
#   logger = logging.getLogger(__name__)
#
#   def ready(self):
#       try:
#           with connection.cursor() as cursor:
#               cursor.execute("SELECT 1")
#           logger.info(f"{self.name} database connection OK")
#       except Exception as e:
#           logger.warning(f"{self.name} database connection failed: {e}")
#
# 4. Don't Perform Database Migrations Here:
#    - ready() runs on every startup, not just during migrations
#    - Use management commands for one-time setup


# =====================
# TROUBLESHOOTING
# =====================
#
# 1. ready() method not being called
#    → Ensure app config is correctly referenced in INSTALLED_APPS
#    → Use explicit path: 'blog.apps.BlogConfig' in settings.py
#    → Restart Django server (changes to apps.py require restart)
#
# 2. "App 'blog' doesn't have a 'BlogConfig' class"
#    → Check that class name exactly matches (case-sensitive)
#    → Verify class inherits from AppConfig
#    → Ensure __init__.py exists in blog directory
#
# 3. Database check runs too early (before database is ready)
#    → This is normal during Docker container startup
#    → The exception catch prevents crashes
#    → Consider using connection.ensure_connection() with timeout
#
# 4. Signals not being registered
#    → Verify signals.py exists in the app directory
#    → Check for syntax errors in signals.py
#    → Ensure signal handlers are decorated with @receiver
#
# 5. print() statements not showing in console
#    → Use logging instead: import logging; logger = logging.getLogger(__name__)
#    → Check that runserver is capturing stdout
#    → Use --verbosity 3 for more output
#
# 6. Module-level database queries causing errors
#    → Move queries into ready() method
#    → Use connection instead of model imports
#    → Wrap in try/except to prevent startup crashes


# =====================
# ALTERNATIVE CONFIGURATION EXAMPLE
# =====================
#
# class BlogConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'blog'
#     verbose_name = 'Blog Management'
#
#     def ready(self):
#         # Only register signals in production to avoid test noise
#         import os
#         if os.environ.get('DJANGO_SETTINGS_MODULE') != 'config.settings.test':
#             from . import signals
#
#         # Set up cache warming (optional)
#         from django.core.cache import cache
#         cache.set('blog_app_ready', True, timeout=60)
