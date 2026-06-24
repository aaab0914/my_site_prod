# urls.py
# ========================================
# Imports
# ========================================

from django.urls import path, include
# path: Function for defining URL patterns in Django
# include: Function for including other URL configurations (e.g., from other apps)

from . import views
# views: The views module containing all view functions for the blog app

from .feeds import LatestPostsFeed, UserPostsFeed
# LatestPostsFeed: The RSS feed class for the blog (global feed)
# UserPostsFeed: The RSS feed class for individual users (user-specific feed)

from .views import PostDeleteView, AudioPostEditView, AudioPostDeleteView
# PostDeleteView: Class-based view for deleting a post (requires authentication and permission)

from . import api_views

# ========================================
# App Namespace
# ========================================

app_name = 'blog'
# app_name: Namespace for the blog app's URLs
# Allows referencing URLs using 'blog:url_name' in templates and views


# ========================================
# URL Patterns
# ========================================

urlpatterns = [
    # ========================================
    # Post Detail Page
    # ========================================
    # URL pattern for displaying a single post detail page
    # Uses year, month, day, and slug to uniquely identify a post
    # Example: /2026/5/3/django-intro/
    path(
        '<int:year>/<int:month>/<int:day>/<slug:post_slug>/',
        views.post_detail,
        name='post_detail'
    ),


    # ========================================
    # Comment Submission
    # ========================================
    # URL pattern for handling comment submission on a specific post
    # Uses post_id to identify which post the comment belongs to
    # Example: /1/comment/ (1 is the post ID)
    path(
        '<int:post_id>/comment/',
        views.add_comment,
        name='post_comment'
    ),


    # ========================================
    # Tag Filtering
    # ========================================
    # URL pattern for displaying posts filtered by a specific tag
    # Uses tag_slug to identify which tag to filter by
    # Example: /tag/django/
    path(
        'tag/<slug:tag_slug>/',
        views.post_list,
        name='post_list_by_tag'
    ),


    # ========================================
    # Main Blog Homepage
    # ========================================
    # URL pattern for the main blog homepage showing all posts
    # Example: / (root path of the blog app)
    path(
        '',
        views.post_list,
        name='all_posts_list'
    ),


    # ========================================
    # RSS Feed
    # ========================================
    # URL pattern for the RSS feed of latest posts
    # Example: /feed/
    path(
        'feed/',
        LatestPostsFeed(),
        name='post_feed'
    ),


    # ========================================
    # Post Search
    # ========================================
    # URL pattern for searching posts by keyword
    # Example: /search/
    path(
        'search/',
        views.post_search,
        name='post_search'
    ),


    # ========================================
    # Post Creation
    # ========================================
    # URL pattern for creating a new post
    # Example: /create/
    path(
        'create/',
        views.post_create,
        name='post_create'
    ),


    # ========================================
    # Post Deletion
    # ========================================
    # URL pattern for deleting a post
    # Uses pk (primary key) to identify the post to delete
    # Example: /1/delete/
    path(
        '<int:pk>/delete/',
        PostDeleteView.as_view(),
        name='post_delete'
    ),

    # URL pattern for the post deletion success page
    # Redirected to after successful deletion
    path(
        'post_delete_success/',
        views.post_delete_success,
        name='post_delete_success'
    ),


    # ========================================
    # Comment Editing
    # ========================================
    # URL pattern for editing a comment
    # Uses post_slug and comment_id to identify the comment
    # Example: /django-intro/1/edit/
    path(
        '<slug:post_slug>/<int:comment_id>/edit/',
        views.edit_comment,
        name='edit_comment'
    ),

    # ========================================
    # Comment Deletion
    # ========================================
    # URL pattern for deleting a comment
    # Uses post_slug and comment_id to identify the comment
    # Example: /django-intro/1/delete/
    path(
        '<slug:post_slug>/<int:comment_id>/delete/',
        views.comment_delete,
        name='comment_delete'
    ),


    # ========================================
    # User App URLs
    # ========================================
    # Includes all URLs from the users app
    # All user-related URLs are prefixed with /users/
    path(
        'users/',
        include('users.urls')
    ),


    # ========================================
    # User-Specific RSS Feed
    # ========================================
    # URL pattern for the RSS feed of a specific user's posts
    # Uses username to identify the user
    # Example: /feed/admin/
    path(
        'feed/<str:username>/',
        UserPostsFeed(),
        name='user_feed'
    ),
    # ===== API ROUTES =====
    path('api/posts/', api_views.PostListAPIView.as_view(), name='api_post_list'),
    path('api/posts/<int:pk>/', api_views.PostDetailAPIView.as_view(), name='api_post_detail'),
    path('api/comments/', api_views.CommentListAPIView.as_view(), name='api_comment_list'),
    path('api/comments/<int:pk>/', api_views.CommentDetailAPIView.as_view(), name='api_comment_detail'),
    path('api/tags/', api_views.tag_list_api, name='api_tag_list'),
    path('api/tags/<slug:slug>/', api_views.tag_detail_api, name='api_tag_detail'),
    path('audio/upload/', views.audio_upload, name='audio_upload'),
    path('audio/list/', views.audio_list, name='audio_list'),
    path('audio/edit/<int:pk>/', AudioPostEditView.as_view(), name='audio_post_edit'),
    path('audio/delete/<int:pk>/', AudioPostDeleteView.as_view(), name='audio_post_delete'),
    path('audio/delete/success/', views.post_delete_success, name='audio_post_delete_success'),
]

# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                             URL ROUTING DIAGRAM                            │
# │                              (My Blog Project)                             │
# └─────────────────────────────────────────────────────────────────────────────┘
#
#                                   ┌─────────────┐
#                                   │   /blog/    │  (all_posts_list)
#                                   └──────┬──────┘
#                                          │
#                          ┌─────────────────┼─────────────────┐
#                          │                 │                 │
#                     ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
#                     │  /tag/  │      │ /feed/  │      │/search/ │
#                     │ <slug>/ │      │         │      │         │
#                     └────┬────┘      └────┬────┘      └────┬────┘
#                          │                │                │
#                          │                │                │
#                     ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
#                     │ /<year>/│      │ /feed/  │      │  Search │
#                     │ <month>/│      │ <user>/ │      │ Results │
#                     │ <day>/  │      │         │      │         │
#                     │ <slug>/ │      └─────────┘      └─────────┘
#                     └────┬────┘
#                          │
#                     ┌────▼────┐
#                     │   Post  │
#                     │  Detail │
#                     └────┬────┘
#                          │
#           ┌─────────────┼─────────────┐
#           │             │             │
#     ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
#     │ /<post_id> │ │ /<slug>/  │ │ /<slug>/  │
#     │ /comment/  │ │ <comment> │ │ <comment> │
#     │            │ │ /edit/    │ │ /delete/  │
#     └────────────┘ └───────────┘ └───────────┘
#           │
#     ┌─────▼─────┐
#     │   Add     │
#     │  Comment  │
#     └───────────┘
#
#
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                         LEGEND                                             │
# ├─────────────────────────────────────────────────────────────────────────────┤
# │ ───►   Direct URL path                                                   │
# │ ───►   Nested URL path (includes parameters)                              │
# │                                                                           │
# │ URL Parameters:                                                           │
# │   <int:year>      - 4-digit year (e.g., 2026)                            │
# │   <int:month>     - Month number (1-12)                                  │
# │   <int:day>       - Day number (1-31)                                    │
# │   <slug:post_slug> - URL-friendly slug of the post (e.g., 'django-intro')│
# │   <int:post_id>   - Post ID (primary key)                                │
# │   <slug:tag_slug> - Slug of a tag (e.g., 'django')                       │
# │   <int:pk>        - Primary key (used for delete)                        │
# │   <str:username>  - Username of a user                                   │
# └─────────────────────────────────────────────────────────────────────────────┘