"""
REST API view definitions for the blog application.
This module provides JSON endpoints for posts, comments, tags, and related resources.
It uses Django REST Framework (DRF) generics, permissions, and filters.
"""

# =============================================================================
# IMPORTS (All imports moved to the top)
# =============================================================================

from django.shortcuts import get_object_or_404
# get_object_or_404: Shortcut to retrieve an object or raise 404 if not found.

from django_filters.rest_framework import DjangoFilterBackend
# DjangoFilterBackend: Provides filter backend integration for DRF views.

from rest_framework import filters, generics, permissions
# filters: DRF search and ordering filter backends.
# generics: DRF generic views (ListCreateAPIView, RetrieveUpdateDestroyAPIView).
# permissions: DRF permission classes (IsAuthenticatedOrReadOnly, AllowAny, etc.).

from rest_framework.decorators import api_view
# api_view: Decorator to convert a function-based view into a DRF API view.

from rest_framework.response import Response
# Response: DRF's HTTP response class for returning JSON data.

from taggit.models import Tag
# Tag: Model from django-taggit representing a single tag.

from .models import Post, Comment
# Post: The main blog post model.
# Comment: User comments attached to posts.

from .serializers import PostCreateSerializer, PostSerializer, CommentSerializer, TagSerializer
# PostCreateSerializer: Serializer for creating new posts (handles tags).
# PostSerializer: Serializer for reading/updating posts.
# CommentSerializer: Serializer for reading/creating comments.
# TagSerializer: Serializer for reading tags.


# =============================================================================
# CUSTOM PERMISSION CLASS
# =============================================================================

class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow authors to edit/delete their own objects.
    Safe methods (GET, HEAD, OPTIONS) are allowed for any authenticated user.
    """
    def has_object_permission(self, request, view, obj):
        """
        Check if the request user has permission to access the object.

        Args:
            request: The HTTP request object.
            view: The view instance making the permission check.
            obj: The model instance being accessed (e.g., a Post).

        Returns:
            bool: True if permission is granted, False otherwise.
        """
        # SAFE_METHODS: GET, HEAD, OPTIONS - always allowed.
        if request.method in permissions.SAFE_METHODS:
            return True
        # For write methods (PUT, PATCH, DELETE), only the author can proceed.
        return request.user.is_authenticated and obj.author == request.user


# =============================================================================
# POST API VIEWS
# =============================================================================

class PostListAPIView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating posts.
    """
    # The base queryset uses the published manager (only PB status).
    queryset = Post.published.all()

    # Serializer class varies between GET (list) and POST (create).
    serializer_class = PostSerializer

    # Permission: authenticated users can create; unauthenticated can only read.
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    # Filter backends: support filtering, searching, and ordering.
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "author__username", "tags__name"]
    search_fields = ["title", "body"]
    ordering_fields = ["publish", "title"]
    ordering = ["-publish"]

    def get_serializer_class(self):
        """
        Return a different serializer for POST requests.
        """
        if self.request.method == "POST":
            return PostCreateSerializer
        return PostSerializer

    def perform_create(self, serializer):
        """
        Assign the current user as the author when creating a new post.
        """
        serializer.save(author=self.request.user)


class PostDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, and deleting a single post.
    """
    queryset = Post.published.all()
    serializer_class = PostSerializer
    # Permission: uses the custom IsAuthorOrReadOnly to protect write operations.
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]


# =============================================================================
# COMMENT API VIEWS
# =============================================================================

class CommentListAPIView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating comments.
    """
    # Only active comments are exposed via the public API.
    queryset = Comment.objects.filter(active=True)
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["post", "name", "active"]

    def perform_create(self, serializer):
        """
        Save the new comment to the database.
        """
        serializer.save()


class CommentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, and deleting a single comment.
    Updates and deletions are disabled; only retrieval is allowed.
    """
    queryset = Comment.objects.filter(active=True)
    serializer_class = CommentSerializer
    permission_classes = [permissions.AllowAny]

    def update(self, request, *args, **kwargs):
        """
        Override update to return 405 Method Not Allowed.
        """
        return Response({"detail": "Comment updates via API are disabled."}, status=405)

    def destroy(self, request, *args, **kwargs):
        """
        Override destroy to return 405 Method Not Allowed.
        """
        return Response({"detail": "Comment deletion via API is disabled."}, status=405)


# =============================================================================
# TAG API VIEWS
# =============================================================================

@api_view(["GET"])
def tag_list_api(request):
    """
    API endpoint to list all tags.

    Args:
        request: The HTTP request object.

    Returns:
        Response: JSON list of all tags ordered by name.
    """
    tags = Tag.objects.all().order_by("name")
    serializer = TagSerializer(tags, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def tag_detail_api(request, slug):
    """
    API endpoint to retrieve a single tag by its slug.

    Args:
        request: The HTTP request object.
        slug: The slug of the tag to retrieve.

    Returns:
        Response: JSON data of the tag, or 404 if not found.
    """
    tag = get_object_or_404(Tag, slug=slug)
    serializer = TagSerializer(tag)
    return Response(serializer.data)

# ┌─────────────────────────────────────────────────────────────────────────────────────┐
# │                                blog/api_views.py                                     │
# │                      (Django REST Framework API Views)                               │
# └─────────────────────────────────────────────────────────────────────────────────────┘
#                                           │
#                                           ▼
# ┌─────────────────────────────────────────────────────────────────────────────────────┐
# │                                 IMPORTS (Dependencies)                               │
# ├─────────────────────────────────────────────────────────────────────────────────────┤
# │  django.shortcuts           │  rest_framework             │  django_filters          │
# │  └─ get_object_or_404       │  ├─ generics                │  └─ DjangoFilterBackend  │
# │  taggit.models              │  ├─ filters                 │  .models                 │
# │  └─ Tag                     │  ├─ permissions             │  ├─ Post                 │
# │  .serializers               │  ├─ decorators              │  └─ Comment              │
# │  ├─ PostCreateSerializer    │  │   └─ api_view            │  .serializers            │
# │  ├─ PostSerializer          │  ├─ response                │  └─ TagSerializer        │
# │  ├─ CommentSerializer       │  │   └─ Response            │                         │
# │  └─ TagSerializer           │                             │                         │
# └─────────────────────────────────────────────────────────────────────────────────────┘
#                                           │
#                                           ▼
#                  ┌──────────────────────────────────────────────────────────────────┐
#                  │                   Classes & Functions                              │
#                  └──────────────────────────────────────────────────────────────────┘
#                                           │
#          ┌────────────────────────────────┼────────────────────────────────┐
#          │                                │                                │
#          ▼                                ▼                                ▼
# ┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐
# │   IsAuthorOrReadOnly     │  │   PostListAPIView        │  │   PostDetailAPIView      │
# │   (Class)                │  │   (Class)               │  │   (Class)               │
# ├─────────────────────────┤  ├─────────────────────────┤  ├─────────────────────────┤
# │ Inherits:               │  │ Inherits:               │  │ Inherits:               │
# │   permissions.Base       │  │   generics.             │  │   generics.             │
# │   Permission             │  │   ListCreateAPIView     │  │   RetrieveUpdateDestroy │
# │                          │  │                         │  │   APIView               │
# │ Purpose:                 │  │ Purpose:               │  │ Purpose:               │
# │   Allow authors to       │  │   List and create      │  │   Retrieve, update,    │
# │   edit/delete their      │  │   posts                │  │   delete posts         │
# │   own objects            │  │                         │  │                         │
# │                          │  │ Overrides:             │  │ Permission:            │
# │ Methods:                 │  │   - get_serializer_    │  │   IsAuthenticatedOr    │
# │   has_object_permission  │  │     class()            │  │   ReadOnly +           │
# │                          │  │   - perform_create()   │  │   IsAuthorOrReadOnly   │
# └─────────────────────────┘  └─────────────────────────┘  └─────────────────────────┘
#                                           │
#           ┌───────────────────────────────┼───────────────────────────────┐
#           ▼                               ▼                               ▼
# ┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐
# │   CommentListAPIView     │  │   CommentDetailAPIView   │  │   tag_list_api          │
# │   (Class)                │  │   (Class)               │  │   (Function)            │
# ├─────────────────────────┤  ├─────────────────────────┤  ├─────────────────────────┤
# │ Inherits:               │  │ Inherits:               │  │ Decorator:              │
# │   generics.             │  │   generics.             │  │   @api_view(["GET"])    │
# │   ListCreateAPIView     │  │   RetrieveUpdateDestroy │  │                         │
# │                          │  │   APIView               │  │ Purpose:               │
# │ Purpose:                 │  │                         │  │   List all tags         │
# │   List and create       │  │ Purpose:               │  │                         │
# │   comments              │  │   Retrieve comments     │  │ Logic:                 │
# │                          │  │                         │  │   Tag.objects.all()    │
# │ Filtering:              │  │ Overrides:             │  │   + TagSerializer       │
# │   - post                │  │   - update() → 405     │  │                         │
# │   - name                │  │   - destroy() → 405    │  │ Returns:               │
# │   - active              │  │                         │  │   JSON list of tags    │
# └─────────────────────────┘  └─────────────────────────┘  └─────────────────────────┘
#                                           │
#                                           ▼
# ┌─────────────────────────────────────────────────────────────────────────────────────┐
# │                            tag_detail_api (Function View)                             │
# ├─────────────────────────────────────────────────────────────────────────────────────┤
# │  Decorator: @api_view(["GET"])                                                       │
# │  Purpose: Retrieve a single tag by its slug                                         │
# │  Logic: get_object_or_404(Tag, slug=slug) + TagSerializer                           │
# │  Returns: JSON data of the tag, or 404 if not found                                 │
# └─────────────────────────────────────────────────────────────────────────────────────┘