# blog/templatetags/blog_tags.py
# =====================
# FILE LOCATION REQUIREMENT
# =====================
#
# This file MUST be placed in a 'templatetags' directory inside the app:
#   blog/
#       __init__.py
#       templatetags/
#           __init__.py
#           blog_tags.py        # <-- This file
#
# The app must be in INSTALLED_APPS for template tags to work.
# After adding/modifying template tags, restart the Django server.

# =====================
# IMPORTS
# =====================

from django import template
# template: Django's template module for creating custom template tags and filters
# Provides Library class for registering custom tags

from django.db.models import Count
# Count: Aggregation function for counting related objects
# Used to count number of comments per post

from django.utils.safestring import mark_safe
# mark_safe: Marks a string as safe for HTML rendering (prevents auto-escaping)
# Essential when returning HTML from Markdown conversion

from ..models import Post
# Relative import of Post model (two levels up)
# .. means go up one directory (from templatetags/ to blog/)

import markdown

# markdown: Library for converting Markdown syntax to HTML
# Converts Markdown text like "# Heading" to "<h1>Heading</h1>"


# =====================
# TEMPLATE TAG LIBRARY INITIALIZATION
# =====================

register = template.Library()


# Creates a template library instance to register custom tags/filters
# The variable name MUST be 'register' (Django convention)
# Django scans this variable in templatetags modules


# =====================
# SIMPLE TAG: TOTAL POSTS
# =====================

@register.simple_tag
def total_posts():
    """
    Simple template tag that returns the total number of published posts.

    Usage in templates:
        {% load blog_tags %}
        {% total_posts %}

    Output example:
        12

    This tag requires no parameters and returns an integer.

    :return: Integer count of all published posts
    """
    # Post.published is the custom manager that filters status=Published
    # .count() executes: SELECT COUNT(*) FROM blog_post WHERE status = 'PB'
    return Post.published.count()


# =====================
# INCLUSION TAG: SHOW LATEST POSTS
# =====================

@register.inclusion_tag('blog/post/latest_posts.html')
def show_latest_posts(count=5):
    """
    Inclusion tag that renders a list of the most recent posts.

    This tag retrieves the latest posts and renders them using a specified template.
    Inclusion tags are more powerful than simple tags because they render a template.

    Usage in templates:
        {% load blog_tags %}
        {% show_latest_posts %}
        {% show_latest_posts 3 %}

    The template should be located at: blog/templates/blog/post/latest_posts.html

    Template variables available:
        - latest_posts: QuerySet of the most recent published posts

    Example template content (latest_posts.html):
        <ul>
            {% for post in latest_posts %}
                <li><a href="{{ post.get_absolute_url }}">{{ post.title }}</a></li>
            {% endfor %}
        </ul>

    :param count: Number of posts to display (default: 5)
    :return: Dictionary containing the latest_posts variable for the template
    """
    # Order posts by publication date descending (newest first)
    # Use published manager (only published posts)
    # Slice to limit the number of results
    latest_posts = Post.published.order_by('-publish')[:count]

    # Return dict where keys become variables in the inclusion template
    return {'latest_posts': latest_posts}


# =====================
# SIMPLE TAG: MOST COMMENTED POSTS
# =====================

@register.simple_tag
def get_most_commented_posts(count=5):
    """
    Simple template tag that returns the posts with the most comments.

    Uses Django aggregation to annotate each post with its comment count,
    then sorts by the highest count and returns the top N posts.

    Usage in templates:
        {% load blog_tags %}
        {% get_most_commented_posts %}
        {% get_most_commented_posts 3 %}

    Output example:
        [<Post: My Popular Post>, <Post: Another Post>, ...]

    Note: Returns a QuerySet (not rendered HTML). To display, iterate in template:
        {% for post in most_commented_posts %}
            <li><a href="{{ post.get_absolute_url }}">{{ post.title }}</a></li>
        {% endfor %}

    :param count: Number of posts to return (default: 5)
    :return: QuerySet of the most commented published posts
    """
    # 1. Start with all published posts
    # 2. Annotate each post with a count of its related comments
    #    total_comments is the alias name for the annotated field
    # 3. Filter to only posts with at least 1 comment
    # 4. Order by total_comments descending (most commented first)
    # 5. Slice to limit results
    return Post.published.annotate(
        total_comments=Count('comments')  # Count comments via related_name='comments'
    ).filter(
        total_comments__gt=0  # Only posts with at least one comment
    ).order_by(
        '-total_comments'  # Descending order (highest first)
    )[:count]  # Limit to 'count' number of results


# =====================
# CUSTOM FILTER: MARKDOWN
# =====================

@register.filter(name='markdown')
def markdown_format(text):
    """
    Template filter that converts Markdown text to HTML.

    This filter allows you to write Markdown in your blog posts and have it
    automatically converted to HTML when rendered.

    Usage in templates:
        {% load blog_tags %}
        {{ post.body|markdown }}

    Example:
        Input: "# Hello\n\nThis is **bold** text."
        Output: <h1>Hello</h1>\n<p>This is <strong>bold</strong> text.</p>

    Important security considerations:
    - mark_safe() marks the output as safe HTML (prevents auto-escaping)
    - Without mark_safe(), Django would escape the HTML tags
    - Be cautious with user-generated content to prevent XSS attacks

    To install markdown library:
        pip install markdown

    :param text: Markdown text string to convert
    :return: HTML string marked as safe for rendering
    """
    # Step 1: markdown.markdown() converts Markdown to HTML string
    # Step 2: mark_safe() tells Django not to auto-escape the HTML
    return mark_safe(markdown.markdown(text))

@register.simple_tag
def user_posts_count(user):
    """
    Returns the number of posts written by the specified user.

    Usage:
        {% user_posts_count request.user %}

    Returns:
        int: Number of posts by the user
    :param user:
    :return:
    """
    if user.is_authenticated:
        return Post.objects.filter(author=user).count()
    return 0
# =====================
# TEMPLATE USAGE EXAMPLE
# =====================
#
# Example base template (blog/base.html):
# {% load blog_tags %}
# <!DOCTYPE html>
# <html>
# <head>
#     <title>My Blog</title>
# </head>
# <body>
#     <header>
#         <h1>My Blog</h1>
#         <p>Total posts: {% total_posts %}</p>
#     </header>
#
#     <aside>
#         <h3>Latest Posts</h3>
#         {% show_latest_posts 5 %}
#
#         <h3>Most Commented</h3>
#         <ul>
#             {% for post in get_most_commented_posts 3 %}
#                 <li><a href="{{ post.get_absolute_url }}">{{ post.title }}</a></li>
#             {% endfor %}
#         </ul>
#     </aside>
#
#     <main>
#         {% block content %}{% endblock %}
#     </main>
# </body>
# </html>


# =====================
# POSSIBLE ENHANCEMENTS
# =====================
#
# 1. Cache the results to reduce database queries:
#
#    from django.core.cache import cache
#
#    @register.simple_tag
#    def total_posts():
#        cache_key = 'total_posts_count'
#        count = cache.get(cache_key)
#        if count is None:
#            count = Post.published.count()
#            cache.set(cache_key, count, 60 * 5)  # Cache for 5 minutes
#        return count
#
# 2. Add a tag for related posts:
#
#    @register.simple_tag
#    def get_related_posts(post, limit=3):
#        return Post.published.filter(tags__in=post.tags.all()).exclude(id=post.id)[:limit]
#
# 3. Add a tag for archives by month:
#
#    @register.simple_tag
#    def get_post_archives():
#        from django.db.models.functions import TruncMonth
#        return Post.published.dates('publish', 'month', order='DESC')
#
# 4. Add a tag for custom query:
#
#    @register.simple_tag(takes_context=True)
#    def get_posts_by_user(context, user):
#        return Post.published.filter(author=user)


# =====================
# TROUBLESHOOTING
# =====================
#
# 1. 'blog_tags' is not a registered tag library
#    → Ensure templatetags directory contains __init__.py
#    → Restart Django server (template tags require restart)
#    → Verify app is in INSTALLED_APPS
#
# 2. ModuleNotFoundError: No module named 'markdown'
#    → Install markdown: pip install markdown
#    → Add to requirements.txt
#
# 3. TemplateDoesNotExist: blog/post/latest_posts.html
#    → Create the template file at correct path
#    → Path is relative to app's template directory
#
# 4. Markdown output is escaped (showing raw HTML)
#    → Ensure you're using mark_safe() in the filter
#    → In template, avoid using |safe manually if using markdown filter
#
# 5. ForeignKey related field name error
#    → 'comments' must match related_name in Comment model
#    → Check Comment model: related_name='comments'
#
# 6. count parameter not working
#    → Ensure default parameter has correct syntax
#    → In template: {% show_latest_posts 3 %} not {% show_latest_posts count=3 %}