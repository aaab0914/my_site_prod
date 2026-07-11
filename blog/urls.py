"""
URL routing configuration for the blog application.

This module defines all URL patterns for the blog app, organized by feature
(posts, comments, audio, api) and combined into a single urlpatterns list.
All URLs use the namespace 'blog' for reverse resolution.
"""

# =============================================================================
# IMPORTS (All imports moved to the top)
# =============================================================================

from django.urls import include, path
# include: Function to include URL patterns from other apps or modules.
# path: Function to define a URL pattern with a route, view, and optional name.

from . import views, api_views
# views: The module containing all function-based and class-based views for the blog.
# api_views: The module containing all REST API view functions and classes.

from .feeds import LatestPostsFeed, UserPostsFeed
# LatestPostsFeed: RSS feed for the latest posts across all authors.
# UserPostsFeed: RSS feed for posts by a specific author.

from .views import PostDeleteView, AudioPostEditView, AudioPostDeleteView
# PostDeleteView: Class-based view for deleting a blog post.
# AudioPostEditView: Class-based view for editing an audio post.
# AudioPostDeleteView: Class-based view for deleting an audio post.


# =============================================================================
# POST URL PATTERNS
# =============================================================================

post_urlpatterns = [
    # The canonical post detail page using date and slug.
    path(
        "<int:year>/<int:month>/<int:day>/<slug:post_slug>/",
        views.post_detail,
        name="post_detail",
    ),
    # Display posts filtered by a specific tag.
    path(
        "tag/<slug:tag_slug>/",
        views.post_list,
        name="post_list_by_tag",
    ),
    # The main blog homepage showing all published posts.
    path(
        "",
        views.post_list,
        name="all_posts_list",
    ),
    # Global RSS feed for latest posts.
    path(
        "feed/",
        LatestPostsFeed(),
        name="post_feed",
    ),
    # User-specific RSS feed for a single author.
    path(
        "feed/<str:username>/",
        UserPostsFeed(),
        name="user_feed",
    ),
    # Search page for finding posts by query.
    path(
        "search/",
        views.post_search,
        name="post_search",
    ),
    # Create a new blog post (requires login).
    path(
        "create/",
        views.post_create,
        name="post_create",
    ),
    path(
        "<int:pk>/edit/",
        views.post_edit,
        name="post_edit",
    ),
    path(
        "media/post-cover/<int:pk>/",
        views.post_cover_image,
        name="post_cover_image",
    ),
    # Delete a post (requires login and ownership/superuser permission).
    path(
        "<int:pk>/delete/",
        PostDeleteView.as_view(),
        name="post_delete",
    ),
    # Success page shown after a post is deleted.
    path(
        "post_delete_success/",
        views.post_delete_success,
        name="post_delete_success",
    ),
]


# =============================================================================
# COMMENT URL PATTERNS
# =============================================================================

comment_urlpatterns = [
    path(
        "media/comment-image/<int:comment_id>/",
        views.comment_image,
        name="comment_image",
    ),
    # Add a new comment to a post (POST only, requires login).
    path(
        "<int:post_id>/comment/",
        views.add_comment,
        name="post_comment",
    ),
    # Edit an existing comment (requires login and ownership).
    path(
        "<slug:post_slug>/<int:comment_id>/edit/",
        views.edit_comment,
        name="edit_comment",
    ),
    # Delete an existing comment (requires login and ownership).
    path(
        "<slug:post_slug>/<int:comment_id>/delete/",
        views.comment_delete,
        name="comment_delete",
    ),
]


# =============================================================================
# AUDIO URL PATTERNS
# =============================================================================

audio_urlpatterns = [
    path(
        "media/audio/<int:pk>/",
        views.audio_file_proxy,
        name="audio_file_proxy",
    ),
    path(
        "media/audio-cover/<int:pk>/",
        views.audio_cover_image_proxy,
        name="audio_cover_image_proxy",
    ),
    # Upload a new audio post (requires login).
    path(
        "audio/upload/",
        views.audio_upload,
        name="audio_upload",
    ),
    # List all audio posts.
    path(
        "audio/list/",
        views.audio_list,
        name="audio_list",
    ),
    # Edit an existing audio post (requires login and ownership).
    path(
        "audio/edit/<int:pk>/",
        AudioPostEditView.as_view(),
        name="audio_post_edit",
    ),
    # Delete an audio post (requires login and ownership).
    path(
        "audio/delete/<int:pk>/",
        AudioPostDeleteView.as_view(),
        name="audio_post_delete",
    ),
    # Success page shown after an audio post is deleted.
    path(
        "audio/delete/success/",
        views.audio_post_delete_success,
        name="audio_post_delete_success",
    ),
]


# =============================================================================
# VIDEO URL PATTERNS
# =============================================================================

video_urlpatterns = [
    path(
        "video/<int:pk>/",
        views.video_detail,
        name="video_detail",
    ),
    path(
        "video/<int:pk>/edit/",
        views.video_edit,
        name="video_edit",
    ),
    path(
        "video/<int:pk>/delete/",
        views.video_delete,
        name="video_delete",
    ),
    path(
        "video/list/",
        views.video_list,
        name="video_list",
    ),
    path(
        "media/video/<int:pk>/",
        views.video_file_proxy,
        name="video_file_proxy",
    ),
    path(
        "video/upload/",
        views.video_upload,
        name="video_upload",
    ),
]


# =============================================================================
# API URL PATTERNS
# =============================================================================

api_urlpatterns = [
    # REST API endpoint for listing and creating posts.
    path(
        "api/posts/",
        api_views.PostListAPIView.as_view(),
        name="api_post_list",
    ),
    # REST API endpoint for retrieving, updating, and deleting a single post.
    path(
        "api/posts/<int:pk>/",
        api_views.PostDetailAPIView.as_view(),
        name="api_post_detail",
    ),
    # REST API endpoint for listing and creating comments.
    path(
        "api/comments/",
        api_views.CommentListAPIView.as_view(),
        name="api_comment_list",
    ),
    # REST API endpoint for retrieving, updating, and deleting a single comment.
    path(
        "api/comments/<int:pk>/",
        api_views.CommentDetailAPIView.as_view(),
        name="api_comment_detail",
    ),
    # REST API endpoint for listing all tags.
    path(
        "api/tags/",
        api_views.tag_list_api,
        name="api_tag_list",
    ),
    # REST API endpoint for retrieving a single tag by its slug.
    path(
        "api/tags/<slug:slug>/",
        api_views.tag_detail_api,
        name="api_tag_detail",
    ),
]


# =============================================================================
# USER APP INCLUSION
# =============================================================================

user_urlpatterns = [
    # Include all URLs from the users app under the /users/ prefix.
    # This mounts the users app's URL configuration at the /users/ URL path.
    path(
        "users/",
        include("users.urls"),
    ),
    path(
        "",
        include(("images.urls", "images"), namespace="images"),
    ),
]


# =============================================================================
# APP NAMESPACE & MASTER URL LIST
# =============================================================================

app_name = "blog"
# app_name: Defines the namespace for the blog app's URL patterns.
# Allows reverse URL resolution using 'blog:url_name' in templates and views.

urlpatterns = [
    # Expand all URL pattern lists into the master urlpatterns list.
    *post_urlpatterns,
    *user_urlpatterns,
    *audio_urlpatterns,
    *video_urlpatterns,
    *comment_urlpatterns,
    *api_urlpatterns,
]

# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                          blog/urls.py                                      │
# │                      (URL Routing Configuration)                           │
# └─────────────────────────────────────────────────────────────────────────────┘
#                                       │
#                                       ▼
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                            IMPORTS (Dependencies)                           │
# ├─────────────────────────────────────────────────────────────────────────────┤
# │  django.urls                │  .feeds                                      │
# │  ├─ include                 │  ├─ LatestPostsFeed                          │
# │  └─ path                    │  └─ UserPostsFeed                           │
# │  .views                     │  .views                                      │
# │  ├─ views                   │  ├─ PostDeleteView                          │
# │  └─ api_views               │  ├─ AudioPostEditView                       │
# │                             │  └─ AudioPostDeleteView                     │
# └─────────────────────────────────────────────────────────────────────────────┘
#                                       │
#                                       ▼
#                  ┌────────────────────────────────────────────────┐
#                  │           URL Pattern Groups                   │
#                  └────────────────────────────────────────────────┘
#                                       │
#          ┌────────────────────────────┼────────────────────────────┐
#          ▼                            ▼                            ▼
# ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
# │   post_urlpatterns   │  │   comment_urlpatterns  │  │   audio_urlpatterns  │
# │   (List)             │  │   (List)             │  │   (List)             │
# ├──────────────────────┤  ├──────────────────────┤  ├──────────────────────┤
# │ Purpose:             │  │ Purpose:             │  │ Purpose:             │
# │   All post-related   │  │   All comment-       │  │   All audio-related  │
# │   URLs               │  │   related URLs       │  │   URLs               │
# │                      │  │                      │  │                      │
# │ Contains:            │  │ Contains:            │  │ Contains:            │
# │   - post_detail      │  │   - post_comment     │  │   - audio_upload     │
# │   - post_list_by_tag │  │   - edit_comment     │  │   - audio_list       │
# │   - all_posts_list   │  │   - comment_delete   │  │   - audio_post_edit  │
# │   - post_feed        │  │                      │  │   - audio_post_delete│
# │   - user_feed        │  │                      │  │   - audio_post_delete│
# │   - post_search      │  │                      │  │     _success         │
# │   - post_create      │  │                      │  │                      │
# │   - post_delete      │  │                      │  │                      │
# │   - post_delete_     │  │                      │  │                      │
# │     success          │  │                      │  │                      │
# └──────────────────────┘  └──────────────────────┘  └──────────────────────┘
#                                       │
#          ┌────────────────────────────┼────────────────────────────┐
#          ▼                            ▼                            ▼
# ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
# │   api_urlpatterns    │  │   user_urlpatterns    │  │   app_name &         │
# │   (List)             │  │   (List)             │  │   urlpatterns        │
# ├──────────────────────┤  ├──────────────────────┤  ├──────────────────────┤
# │ Purpose:             │  │ Purpose:             │  │ Purpose:             │
# │   All REST API URLs  │  │   Include users app  │  │   Combine all groups │
# │                      │  │   URLs               │  │   and set namespace  │
# │ Contains:            │  │                      │  │                      │
# │   - api_post_list    │  │ Contains:            │  │ Final Structure:     │
# │   - api_post_detail  │  │   users/ (include)   │  │   urlpatterns = [    │
# │   - api_comment_list │  │                      │  │     *post_urlpatterns │
# │   - api_comment_     │  │                      │  │     *comment_url...  │
# │     detail           │  │                      │  │     *user_urlpatterns│
# │   - api_tag_list     │  │                      │  │     *api_urlpatterns │
# │   - api_tag_detail   │  │                      │  │     *audio_url...    │
# │                      │  │                      │  │   ]                 │
# └──────────────────────┘  └──────────────────────┘  └──────────────────────┘
