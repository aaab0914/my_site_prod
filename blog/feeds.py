from django.contrib.auth.models import User
from django.contrib.syndication.views import Feed
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import truncatewords
from django.urls import reverse_lazy
from django.utils.html import strip_tags

from .models import Post


class LatestPostsFeed(Feed):
    title = "My Blog"
    link = reverse_lazy("blog:all_posts_list")
    description = "New Posts of My Blog."

    def items(self):
        return Post.published.all()[:5]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return truncatewords(strip_tags(item.get_markdown_body()), 30) + "..."

    def item_pubdate(self, item):
        return item.publish


class UserPostsFeed(Feed):
    def get_object(self, request, username):
        return get_object_or_404(User, username=username)

    def title(self, obj):
        return f"{obj.username}'s Posts"

    def link(self, obj):
        return f"/blog/user/{obj.username}/"

    def description(self, obj):
        return f"Latest posts from {obj.username}"

    def items(self, obj):
        return Post.published.filter(author=obj).order_by("-publish")[:5]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return truncatewords(strip_tags(item.get_markdown_body()), 30) + "..."

    def item_pubdate(self, item):
        return item.publish
