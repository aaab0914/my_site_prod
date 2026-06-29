# blog/urls.py
# ================================================================
# URL Configuration for Blog Application
# ================================================================
# This module defines all URL patterns for the blog application.
# It maps HTTP requests to appropriate view functions or class-based views.
# The app_name = 'blog' establishes a namespace for reverse URL resolution.
# ================================================================

# ================================================================
# IMPORTS
# ================================================================

# path: Function for defining URL patterns with optional parameters
#       Syntax: path(route, view, name=None)
#       route: URL string pattern (can contain dynamic parameters)
#       view: Callable view function or View class
#       name: Unique identifier for reverse URL lookup

# include: Function for including other URL configurations
#          Used to mount other apps' URLconfs at a specific prefix
#          Example: path('users/', include('users.urls'))
from django.urls import path, include

# views: The views module containing all view functions for the blog app
#        Imported as a module to access functions like post_list, post_detail
from . import views

# feeds: RSS feed classes for the blog
# LatestPostsFeed: Global RSS feed containing latest posts from all users
# UserPostsFeed: User-specific RSS feed showing posts from a single author
from .feeds import LatestPostsFeed, UserPostsFeed

# Class-based views for post deletion and audio post management
# PostDeleteView: Handles deletion of blog posts (requires authentication)
# AudioPostEditView: Handles editing of audio posts
# AudioPostDeleteView: Handles deletion of audio posts
from .views import PostDeleteView, AudioPostEditView, AudioPostDeleteView

# api_views: Module containing REST API view functions and classes
#            Provides JSON endpoints for posts, comments, and tags
from . import api_views


# ================================================================
# APP NAMESPACE
# ================================================================

# app_name: Namespace for the blog app's URL patterns
# Purpose:
#   1. Prevents URL name conflicts between different apps
#   2. Enables reverse URL resolution using 'blog:url_name'
#   3. Example in templates: {% url 'blog:post_detail' year=2026 month=5 day=3 slug='django-intro' %}
#   4. Example in views: reverse('blog:post_detail', args=[2026, 5, 3, 'django-intro'])
app_name = 'blog'


# ================================================================
# URL PATTERNS
# ================================================================

urlpatterns = [

    # ============================================================
    # POST DETAIL PAGE
    # ============================================================
    # URL: /<int:year>/<int:month>/<int:day>/<slug:post_slug>/
    # View: post_detail (function-based view)
    # Name: 'post_detail'
    # Purpose: Display a single blog post identified by its publication date and slug
    # Example: /2026/5/3/django-intro/
    # URL Parameters:
    #   year: 4-digit publication year (e.g., 2026)
    #   month: Publication month (1-12)
    #   day: Publication day (1-31)
    #   post_slug: URL-friendly title (auto-generated from title)
    path(
        '<int:year>/<int:month>/<int:day>/<slug:post_slug>/',
        views.post_detail,
        name='post_detail'
    ),

    # ============================================================
    # COMMENT SUBMISSION
    # ============================================================
    # URL: /<int:post_id>/comment/
    # View: add_comment (function-based view)
    # Name: 'post_comment'
    # Purpose: Handle comment submission for a specific post
    # Example: /42/comment/
    # URL Parameters:
    #   post_id: Primary key of the post being commented on
    # HTTP Methods: POST (form submission)
    # Redirects to post_detail on success
    path(
        '<int:post_id>/comment/',
        views.add_comment,
        name='post_comment'
    ),

    # ============================================================
    # TAG FILTERING
    # ============================================================
    # URL: /tag/<slug:tag_slug>/
    # View: post_list (function-based view)
    # Name: 'post_list_by_tag'
    # Purpose: Display all posts filtered by a specific tag
    # Example: /tag/django/
    # URL Parameters:
    #   tag_slug: Slug of the tag (auto-generated from tag name)
    # Uses the same post_list view as homepage, with tag filtering
    path(
        'tag/<slug:tag_slug>/',
        views.post_list,
        name='post_list_by_tag'
    ),

    # ============================================================
    # MAIN BLOG HOMEPAGE
    # ============================================================
    # URL: /
    # View: post_list (function-based view)
    # Name: 'all_posts_list'
    # Purpose: Display the main blog homepage with all published posts
    # Example: / (root path of the blog app)
    # Pagination: Posts are paginated (default: 3 posts per page)
    # Ordering: Newest posts first (by publish date descending)
    path(
        '',
        views.post_list,
        name='all_posts_list'
    ),

    # ============================================================
    # RSS FEED - GLOBAL
    # ============================================================
    # URL: /feed/
    # View: LatestPostsFeed (class-based feed)
    # Name: 'post_feed'
    # Purpose: Generate RSS feed of the latest blog posts
    # Example: /feed/
    # Response: application/rss+xml
    # Contains: Latest 5 posts with title, description, and publication date
    path(
        'feed/',
        LatestPostsFeed(),
        name='post_feed'
    ),

    # ============================================================
    # POST SEARCH
    # ============================================================
    # URL: /search/
    # View: post_search (function-based view)
    # Name: 'post_search'
    # Purpose: Search posts by title or content
    # Example: /search/?query=python
    # Query Parameter: ?query=keyword
    # Uses Django's PostgreSQL full-text search (or basic contains)
    path(
        'search/',
        views.post_search,
        name='post_search'
    ),

    # ============================================================
    # POST CREATION
    # ============================================================
    # URL: /create/
    # View: post_create (function-based view)
    # Name: 'post_create'
    # Purpose: Display form and handle creation of new blog posts
    # Example: /create/
    # Access: Login required (@login_required decorator)
    # HTTP Methods: GET (display form), POST (save post)
    path(
        'create/',
        views.post_create,
        name='post_create'
    ),

    # ============================================================
    # POST DELETION
    # ============================================================
    # URL: /<int:pk>/delete/
    # View: PostDeleteView (class-based view)
    # Name: 'post_delete'
    # Purpose: Handle deletion of a blog post
    # Example: /42/delete/
    # URL Parameters:
    #   pk: Primary key of the post to delete
    # Access: Login required + permission check (DeletePostPermission)
    # HTTP Methods: GET (confirmation), POST (actual deletion)
    path(
        '<int:pk>/delete/',
        PostDeleteView.as_view(),
        name='post_delete'
    ),

    # ============================================================
    # POST DELETION SUCCESS
    # ============================================================
    # URL: /post_delete_success/
    # View: post_delete_success (function-based view)
    # Name: 'post_delete_success'
    # Purpose: Display success page after post deletion
    # Example: /post_delete_success/
    # Redirect target after successful deletion
    path(
        'post_delete_success/',
        views.post_delete_success,
        name='post_delete_success'
    ),

    # ============================================================
    # COMMENT EDITING
    # ============================================================
    # URL: /<slug:post_slug>/<int:comment_id>/edit/
    # View: edit_comment (function-based view)
    # Name: 'edit_comment'
    # Purpose: Edit an existing comment
    # Example: /django-intro/5/edit/
    # URL Parameters:
    #   post_slug: Slug of the post containing the comment
    #   comment_id: Primary key of the comment being edited
    # Access: Comment owner or superuser
    path(
        '<slug:post_slug>/<int:comment_id>/edit/',
        views.edit_comment,
        name='edit_comment'
    ),

    # ============================================================
    # COMMENT DELETION
    # ============================================================
    # URL: /<slug:post_slug>/<int:comment_id>/delete/
    # View: comment_delete (function-based view)
    # Name: 'comment_delete'
    # Purpose: Delete an existing comment
    # Example: /django-intro/5/delete/
    # URL Parameters:
    #   post_slug: Slug of the post containing the comment
    #   comment_id: Primary key of the comment being deleted
    # Access: Comment owner or superuser
    path(
        '<slug:post_slug>/<int:comment_id>/delete/',
        views.comment_delete,
        name='comment_delete'
    ),

    # ============================================================
    # USER APP URLS (INCLUDED)
    # ============================================================
    # URL: /users/
    # View: All URLs from users app (included via include())
    # Example: /users/login/, /users/register/, /users/profile/
    # Prefix: 'users/' is added to all user app URLs
    # This mounts the user app's URLconf at the '/users/' prefix
    path(
        'users/',
        include('users.urls')
    ),

    # ============================================================
    # RSS FEED - USER SPECIFIC
    # ============================================================
    # URL: /feed/<str:username>/
    # View: UserPostsFeed (class-based feed)
    # Name: 'user_feed'
    # Purpose: Generate RSS feed of posts from a specific user
    # Example: /feed/admin/
    # URL Parameters:
    #   username: Username of the author
    # Response: application/rss+xml
    # Contains: Latest posts by the specified user
    path(
        'feed/<str:username>/',
        UserPostsFeed(),
        name='user_feed'
    ),

    # ============================================================
    # REST API ROUTES
    # ============================================================
    # Purpose: Provide JSON-based REST API endpoints for client-side apps
    # All API routes are prefixed with '/api/' for clarity

    # Endpoint: GET /api/posts/
    # View: PostListAPIView (class-based view)
    # Name: 'api_post_list'
    # Purpose: Retrieve a paginated list of all published posts
    # Response: JSON with post objects (id, title, slug, body, author, publish, etc.)
    path('api/posts/', api_views.PostListAPIView.as_view(), name='api_post_list'),

    # Endpoint: GET /api/posts/<int:pk>/
    # View: PostDetailAPIView (class-based view)
    # Name: 'api_post_detail'
    # Purpose: Retrieve a single post by its primary key
    # Example: /api/posts/42/
    path('api/posts/<int:pk>/', api_views.PostDetailAPIView.as_view(), name='api_post_detail'),

    # Endpoint: GET /api/comments/
    # View: CommentListAPIView (class-based view)
    # Name: 'api_comment_list'
    # Purpose: Retrieve a list of all comments (with filtering options)
    # Optional Query Params: ?post_id=42 (filter by post)
    path('api/comments/', api_views.CommentListAPIView.as_view(), name='api_comment_list'),

    # Endpoint: GET /api/comments/<int:pk>/
    # View: CommentDetailAPIView (class-based view)
    # Name: 'api_comment_detail'
    # Purpose: Retrieve a single comment by its primary key
    # Example: /api/comments/5/
    path('api/comments/<int:pk>/', api_views.CommentDetailAPIView.as_view(), name='api_comment_detail'),

    # Endpoint: GET /api/tags/
    # View: tag_list_api (function-based view)
    # Name: 'api_tag_list'
    # Purpose: Retrieve a list of all tags
    # Response: JSON with tag objects (id, name, slug, post_count)
    path('api/tags/', api_views.tag_list_api, name='api_tag_list'),

    # Endpoint: GET /api/tags/<slug:slug>/
    # View: tag_detail_api (function-based view)
    # Name: 'api_tag_detail'
    # Purpose: Retrieve a single tag by its slug
    # Example: /api/tags/django/
    path('api/tags/<slug:slug>/', api_views.tag_detail_api, name='api_tag_detail'),

    # ============================================================
    # AUDIO POST ROUTES
    # ============================================================
    # Purpose: Management of audio posts (music uploads)

    # Endpoint: GET/POST /audio/upload/
    # View: audio_upload (function-based view)
    # Name: 'audio_upload'
    # Purpose: Upload a new audio file post
    # Access: Login required
    # HTTP Methods: GET (display form), POST (upload file)
    path('audio/upload/', views.audio_upload, name='audio_upload'),

    # Endpoint: GET /audio/list/
    # View: audio_list (function-based view)
    # Name: 'audio_list'
    # Purpose: Display a list of all audio posts
    # Access: Login required (or public, depending on business logic)
    path('audio/list/', views.audio_list, name='audio_list'),

    # Endpoint: GET/POST /audio/edit/<int:pk>/
    # View: AudioPostEditView (class-based view)
    # Name: 'audio_post_edit'
    # Purpose: Edit an existing audio post
    # Example: /audio/edit/5/
    # Access: Audio post owner or superuser
    path('audio/edit/<int:pk>/', AudioPostEditView.as_view(), name='audio_post_edit'),

    # Endpoint: GET/POST /audio/delete/<int:pk>/
    # View: AudioPostDeleteView (class-based view)
    # Name: 'audio_post_delete'
    # Purpose: Delete an audio post
    # Example: /audio/delete/5/
    # Access: Audio post owner or superuser
    path('audio/delete/<int:pk>/', AudioPostDeleteView.as_view(), name='audio_post_delete'),

    # Endpoint: GET /audio/delete/success/
    # View: post_delete_success (function-based view)
    # Name: 'audio_post_delete_success'
    # Purpose: Display success page after audio post deletion
    # Redirect target after successful deletion
    path('audio/delete/success/', views.post_delete_success, name='audio_post_delete_success'),
]

# ================================================================
# URL ROUTING DIAGRAM (TEXT VISUALIZATION)
# ================================================================
#
#                              ┌─────────────────────────────────────────────────────────────────┐
#                              │                    BLOG URL ROUTING TREE                       │
#                              └─────────────────────────────────────────────────────────────────┘
#
#                                                 /blog/
#                                                    │
#                          ┌─────────────────────────┼─────────────────────────┐
#                          │                         │                         │
#                          ▼                         ▼                         ▼
#                    ┌───────────┐            ┌───────────┐            ┌───────────┐
#                    │   /       │            │  /tag/    │            │  /feed/   │
#                    │all_posts_ │            │ <tag_slug>│            │           │
#                    │  list     │            │           │            │           │
#                    └───────────┘            └───────────┘            └───────────┘
#                          │                         │                         │
#                          │                         │                         │
#                          ▼                         ▼                         ▼
#                    ┌───────────┐            ┌───────────┐            ┌───────────┐
#                    │  /create/ │            │ post_list │            │ Latest    │
#                    │  post_    │            │ by tag    │            │ Posts     │
#                    │  create   │            └───────────┘            │ Feed      │
#                    └───────────┘                                    └───────────┘
#                          │                         │                         │
#                    ┌───────────┐                    │                         │
#                    │  /search/ │                    │                         │
#                    │  post_    │                    │                         │
#                    │  search   │                    │                         │
#                    └───────────┘                    │                         │
#                                                     │                         │
#                          ┌──────────────────────────┼─────────────────────────┘
#                          │                          │
#                          ▼                          ▼
#                    ┌───────────────────────────────────────────────────────────┐
#                    │      /<int:year>/<int:month>/<int:day>/<slug:post_slug>/ │
#                    │                     post_detail                          │
#                    └───────────────────────────────────────────────────────────┘
#                                                     │
#                              ┌──────────────────────┼──────────────────────┐
#                              │                      │                      │
#                              ▼                      ▼                      ▼
#                    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
#                    │  /<int:post_id>/ │  │  /<slug:post_   │  │  /<slug:post_   │
#                    │   /comment/     │  │   slug>/<int:   │  │   slug>/<int:   │
#                    │  add_comment    │  │   comment_id>/  │  │   comment_id>/  │
#                    │                 │  │   /edit/        │  │   /delete/      │
#                    └─────────────────┘  │  edit_comment   │  │  comment_delete │
#                              │          └─────────────────┘  └─────────────────┘
#                              ▼
#                    ┌─────────────────┐
#                    │  /<int:pk>/     │
#                    │  /delete/       │
#                    │  PostDeleteView │
#                    └─────────────────┘
#                              │
#                              ▼
#                    ┌─────────────────┐
#                    │ /post_delete_   │
#                    │  success/       │
#                    │ post_delete_    │
#                    │ success         │
#                    └─────────────────┘
#
#                              ┌─────────────────────────────────────────────────────────────────┐
#                              │                    API ROUTES (REST)                            │
#                              └─────────────────────────────────────────────────────────────────┘
#
#                    ┌───────────────────────────────────────────────────────────────────────────┐
#                    │                                /api/                                     │
#                    └───────────────────────────────────────────────────────────────────────────┘
#                              │                          │                          │
#                              ▼                          ▼                          ▼
#                    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────────┐
#                    │  /posts/        │  │  /comments/     │  │  /tags/                         │
#                    │  PostList       │  │  CommentList    │  │  tag_list_api                   │
#                    │  APIView        │  │  APIView        │  └─────────────────────────────────┘
#                    └─────────────────┘  └─────────────────┘                    │
#                              │                          │                          │
#                              ▼                          ▼                          ▼
#                    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────────┐
#                    │  /posts/<int:   │  │  /comments/<int:│  │  /tags/<slug:slug>/             │
#                    │   pk>/          │  │   pk>/          │  │  tag_detail_api                 │
#                    │  PostDetail     │  │  CommentDetail  │  └─────────────────────────────────┘
#                    │  APIView        │  │  APIView        │
#                    └─────────────────┘  └─────────────────┘
#
#                              ┌─────────────────────────────────────────────────────────────────┐
#                              │                    AUDIO ROUTES                                 │
#                              └─────────────────────────────────────────────────────────────────┘
#
#                    ┌───────────────────────────────────────────────────────────────────────────┐
#                    │                                /audio/                                    │
#                    └───────────────────────────────────────────────────────────────────────────┘
#                              │                          │                          │
#                              ▼                          ▼                          ▼
#                    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────────┐
#                    │  /upload/       │  │  /list/         │  │  /edit/<int:pk>/               │
#                    │  audio_upload   │  │  audio_list     │  │  AudioPostEditView              │
#                    └─────────────────┘  └─────────────────┘  └─────────────────────────────────┘
#                              │                          │                          │
#                              ▼                          ▼                          ▼
#                    ┌───────────────────────────────────────────────────────────────────────────┐
#                    │                    /delete/<int:pk>/  AudioPostDeleteView                   │
#                    │                    /delete/success/   post_delete_success                  │
#                    └───────────────────────────────────────────────────────────────────────────┘
#
#                              ┌─────────────────────────────────────────────────────────────────┐
#                              │                    USER ROUTES (INCLUDED)                       │
#                              └─────────────────────────────────────────────────────────────────┘
#
#                    ┌───────────────────────────────────────────────────────────────────────────┐
#                    │                                /users/                                    │
#                    │              (All routes from users.urls included via include)             │
#                    │                                                                           │
#                    │  /users/login/    → Login page                                            │
#                    │  /users/register/ → Registration page                                     │
#                    │  /users/profile/  → Profile page                                          │
#                    │  /users/logout/   → Logout redirect                                       │
#                    │  /users/delete/   → Account deletion                                      │
#                    └───────────────────────────────────────────────────────────────────────────┘

# ================================================================
# URL PARAMETER REFERENCE
# ================================================================
#
# ┌─────────────────────────────────────────────────────────────────────────────────┐
# │  Parameter Type  │  Format                       │  Example                    │
# ├─────────────────────────────────────────────────────────────────────────────────┤
# │  <int:year>      │  4-digit year                │  2026                       │
# │  <int:month>     │  1-12                        │  5                          │
# │  <int:day>       │  1-31                        │  3                          │
# │  <slug:post_slug>│  URL-friendly title          │  django-intro               │
# │  <int:post_id>   │  Primary key (integer)       │  42                         │
# │  <slug:tag_slug> │  URL-friendly tag name       │  django                     │
# │  <int:pk>        │  Primary key (integer)       │  42                         │
# │  <str:username>  │  Username string             │  admin                      │
# └─────────────────────────────────────────────────────────────────────────────────┘

# ================================================================
# URL NAMESPACE REFERENCE
# ================================================================
#
# ┌─────────────────────────────────────────────────────────────────────────────────┐
# │  URL Name                  │  URL Pattern                                      │
# ├─────────────────────────────────────────────────────────────────────────────────┤
# │  blog:all_posts_list       │  /                                               │
# │  blog:post_detail          │  /<year>/<month>/<day>/<slug>/                   │
# │  blog:post_comment         │  /<post_id>/comment/                             │
# │  blog:post_list_by_tag     │  /tag/<tag_slug>/                                │
# │  blog:post_feed            │  /feed/                                          │
# │  blog:user_feed            │  /feed/<username>/                               │
# │  blog:post_search          │  /search/                                        │
# │  blog:post_create          │  /create/                                        │
# │  blog:post_delete          │  /<int:pk>/delete/                               │
# │  blog:post_delete_success  │  /post_delete_success/                           │
# │  blog:edit_comment         │  /<slug:post_slug>/<int:comment_id>/edit/        │
# │  blog:comment_delete       │  /<slug:post_slug>/<int:comment_id>/delete/      │
# │  blog:audio_upload         │  /audio/upload/                                  │
# │  blog:audio_list           │  /audio/list/                                    │
# │  blog:audio_post_edit      │  /audio/edit/<int:pk>/                           │
# │  blog:audio_post_delete    │  /audio/delete/<int:pk>/                         │
# │  blog:audio_post_delete_   │  /audio/delete/success/                          │
# │            success         │                                                  │
# │  blog:api_post_list        │  /api/posts/                                     │
# │  blog:api_post_detail      │  /api/posts/<int:pk>/                            │
# │  blog:api_comment_list     │  /api/comments/                                  │
# │  blog:api_comment_detail   │  /api/comments/<int:pk>/                         │
# │  blog:api_tag_list         │  /api/tags/                                      │
# │  blog:api_tag_detail       │  /api/tags/<slug:slug>/                          │
# └─────────────────────────────────────────────────────────────────────────────────┘