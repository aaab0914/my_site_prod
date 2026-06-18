# blog/sitemaps.py
# ========================================
# Imports
# ========================================

from django.contrib.sitemaps import Sitemap
# Sitemap: Base class for creating sitemaps in Django

from .models import Post
# Post: The main blog post model (imported from the current app)


# ========================================
# Sitemap Configuration
# ========================================

class PostSitemap(Sitemap):
    """
    Sitemap configuration for the Post model.
    """
    changefreq = 'weekly'
    priority = 0.9

    def items(self):
        """
        Return the queryset of published posts.
        """
        return Post.published.all()

    def lastmod(self, obj):
        """
        Return the last modified date of the post.
        """
        return obj.updated