# blog/feeds.py
# ========================================
# Imports
# ========================================

from django.contrib.syndication.views import Feed
# Feed: Base class for creating RSS/Atom feeds in Django

from django.urls import reverse_lazy
# reverse_lazy: Lazy version of reverse() for generating URLs when the URL configuration is not yet loaded

from django.shortcuts import get_object_or_404
# get_object_or_404: Retrieves an object or raises a 404 error if not found

from django.contrib.auth.models import User
# User: The built-in user model

from django.utils.html import strip_tags
# strip_tags: Utility function to remove HTML tags from a string

from django.template.defaultfilters import truncatewords
# truncatewords: Template filter that truncates plain text to a specified number of words

from .models import Post
# Post: The main blog post model (imported from the current app)


# ========================================
# RSS Feed Classes
# ========================================

class LatestPostsFeed(Feed):
    """
    RSS feed for the latest blog posts.

    This feed provides the 5 most recent published posts.
    It is accessible at /blog/feed/ and can be subscribed to in any RSS reader.

    Attributes:
        title: The title of the RSS feed.
        link: The link to the blog's homepage.
        description: A description of the feed.
    """

    # The title of the RSS feed (displayed in RSS readers)
    title = 'My Blog'

    # The link to the blog's homepage (used as the feed's base URL)
    # Uses reverse_lazy to avoid circular import issues
    link = reverse_lazy('blog:all_posts_list')

    # A short description of the feed
    description = 'New Posts of My Blog.'

    def items(self):
        """
        Return the queryset of posts to include in the feed.

        Returns the 5 most recent published posts.
        """
        return Post.published.all()[:5]

    def item_title(self, item):
        """
        Return the title of a post for the feed.

        Args:
            item: A Post instance
        Returns:
            The title of the post as a string
        """
        return item.title

    def item_description(self, item):
        """
        Return the description (excerpt) of a post for the feed.

        Converts Markdown to HTML, strips all HTML tags, and truncates to 30 words.

        Args:
            item: A Post instance
        Returns:
            A plain text excerpt of the post
        """
        # Convert Markdown to HTML, then strip all HTML tags
        plain_text = strip_tags(item.get_markdown_body())
        # Truncate to 30 words and add ellipsis
        return truncatewords(plain_text, 30) + '...'

    def item_pubdate(self, item):
        """
        Return the publication date of a post for the feed.

        Args:
            item: A Post instance
        Returns:
            The publication date as a datetime object
        """
        return item.publish


class UserPostsFeed(Feed):
    """
    RSS feed for a specific user's posts.

    This feed provides the 5 most recent posts authored by a specific user.
    It is accessible at /blog/feed/<username>/ and can be subscribed to
    in any RSS reader.

    Attributes:
        title: Dynamically generated title based on the user's username.
        link: Dynamically generated link to the user's profile page.
        description: Dynamically generated description based on the user's username.
    """

    def get_object(self, request, username):
        """
        Retrieve the user object from the username URL parameter.

        Args:
            request: HTTP request object
            username: The username from the URL
        Returns:
            A User instance
        Raises:
            Http404: If the user does not exist
        """
        return get_object_or_404(User, username=username)

    def title(self, obj):
        """
        Return the title of the RSS feed.

        Args:
            obj: A User instance
        Returns:
            A string title containing the user's username
        """
        return f"{obj.username}'s Posts"

    def link(self, obj):
        """
        Return the link to the user's profile page.

        Args:
            obj: A User instance
        Returns:
            A string URL to the user's profile page
        """
        return f"/blog/user/{obj.username}/"

    def description(self, obj):
        """
        Return a description of the feed.

        Args:
            obj: A User instance
        Returns:
            A string description of the feed
        """
        return f"Latest posts from {obj.username}"

    def items(self, obj):
        """
        Return the queryset of posts to include in the feed.

        Filters posts by the specified author and returns the 5 most recent.

        Args:
            obj: A User instance
        Returns:
            A QuerySet of Post objects
        """
        return Post.published.filter(author=obj).order_by('-publish')[:5]

    def item_title(self, item):
        """
        Return the title of a post for the feed.

        Args:
            item: A Post instance
        Returns:
            The title of the post as a string
        """
        return item.title

    def item_description(self, item):
        """
        Return the description (excerpt) of a post for the feed.

        Converts Markdown to HTML, strips all HTML tags, and truncates to 30 words.

        Args:
            item: A Post instance
        Returns:
            A plain text excerpt of the post
        """
        # Convert Markdown to HTML, then strip all HTML tags
        plain_text = strip_tags(item.get_markdown_body())
        # Truncate to 30 words and add ellipsis
        return truncatewords(plain_text, 30) + '...'

    def item_pubdate(self, item):
        """
        Return the publication date of a post for the feed.

        Args:
            item: A Post instance
        Returns:
            The publication date as a datetime object
        """
        return item.publish

# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                             FEEDS RELATIONSHIP DIAGRAM                      │
# │                              (My Blog Project)                              │
# └─────────────────────────────────────────────────────────────────────────────┘
#
#                      ┌──────────────────────────────────────────────────────┐
#                      │       django.contrib.syndication.views.Feed          │
#                      │                 (Base Class)                         │
#                      └─────────────────┬────────────────────────────────────┘
#                                        │
#                                        │ Inherits
#                                        │
#           ┌────────────────────────────┼────────────────────────────┐
#           │                            │                            │
#           ▼                            ▼                            ▼
# ┌─────────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐
# │   LatestPostsFeed   │      │    UserPostsFeed    │      │    Other Feeds      │
# ├─────────────────────┤      ├─────────────────────┤      ├─────────────────────┤
# │  title: "My Blog"   │      │  title: dynamic     │      │  (Future extension) │
# │  link: reverse_lazy │      │  link: dynamic      │      │                     │
# │  description: "..." │      │  description: "..." │      │                     │
# │  items: 5 latest    │      │  items: 5 per user  │      │                     │
# │                     │      │                     │      │                     │
# │  item_title()       │      │  item_title()       │      │                     │
# │  item_description() │      │  item_description() │      │                     │
# │  item_pubdate()     │      │  item_pubdate()     │      │                     │
# └─────────────────────┘      └─────────────────────┘      └─────────────────────┘
#        │                            │
#        │                            │
#        ▼                            ▼
# ┌─────────────────────┐      ┌─────────────────────┐
# │  Uses Post.published│      │  Uses Post.published│
# │  .all()[:5]         │      │  .filter(author=obj)│
# └─────────────────────┘      └─────────────────────┘
#        │                            │
#        │                            │
#        ▼                            ▼
# ┌─────────────────────┐      ┌─────────────────────┐
# │  URL: /blog/feed/   │      │  URL: /blog/feed/   │
# │                     │      │  <username>/        │
# └─────────────────────┘      └─────────────────────┘
#
#
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                         LEGEND                                              │
# ├─────────────────────────────────────────────────────────────────────────────┤
# │ ───►   Inheritance (parent-child relationship)                              │
# │ ───►   Data flow (what data is used by each class)                          │
# │ ───►   URL access (where each feed is accessible)                           │
# │                                                                             │
# │ Feed Classes:                                                               │
# │   - LatestPostsFeed: Global feed for all posts                              │
# │   - UserPostsFeed: User-specific feed for a single user                     │
# └─────────────────────────────────────────────────────────────────────────────┘