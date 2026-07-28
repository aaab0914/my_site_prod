"""
REST API view definitions for the blog application.
This module provides JSON endpoints for posts, comments, tags, and related resources.
It uses Django REST Framework (DRF) generics, permissions, and filters.
"""

from django.db.models import Case, IntegerField, When
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from taggit.models import Tag

from .models import Post, Comment
from .search import comment_search_result_ids, search_result_ids
from .serializers import PostCreateSerializer, PostSerializer, CommentSerializer, CommentWriteSerializer, TagSerializer
from my_site.media_helpers import invalidate_cache_keys, invalidate_public_view_caches


def _invalidate_blog_public_views():
    invalidate_public_view_caches(
        "view:site_index",
        "view:post_search:empty",
        "view:audio_list:1",
        "view:video_list:1",
        "view:gallery_list:page:1",
        "view:album_list:page:1",
        "view:post_list:1:all:newest",
        "view:post_list:1:all:oldest",
        "view:post_list:1:all:title_az",
        "view:post_list:1:all:title_za",
    )


class IsAuthorOrAdminOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        owner = getattr(obj, 'author', None)
        return request.user.is_authenticated and (owner == request.user or request.user.is_staff)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class RedirectAnonymousUsersToBlogMixin:
    redirect_anonymous_safe_methods = False

    def dispatch(self, request, *args, **kwargs):
        drf_request = self.initialize_request(request, *args, **kwargs)
        self.request = drf_request
        self.headers = self.default_response_headers

        try:
            self.initial(drf_request, *args, **kwargs)
            should_redirect = (
                not drf_request.user.is_authenticated
                and self.redirect_anonymous_safe_methods
                and drf_request.method in permissions.SAFE_METHODS
            )
            if should_redirect:
                response = redirect("blog:all_posts_list")
            else:
                handler = getattr(self, drf_request.method.lower(), self.http_method_not_allowed)
                response = handler(drf_request, *args, **kwargs)
        except Exception as exc:
            response = self.handle_exception(exc)

        self.response = self.finalize_response(drf_request, response, *args, **kwargs)
        return self.response


class PostListAPIView(RedirectAnonymousUsersToBlogMixin, generics.ListCreateAPIView):
    pagination_class = StandardResultsSetPagination
    queryset = Post.published.select_related("author").prefetch_related("tags")
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["status", "author__username", "tags__name"]
    ordering_fields = ["publish", "title"]
    ordering = ["-publish"]

    def get_queryset(self):
        queryset = super().get_queryset()
        search_term = (self.request.GET.get("search") or "").strip()
        if not search_term:
            return queryset
        result_ids, _backend = search_result_ids(search_term)
        if not result_ids:
            return queryset.none()
        relevance = Case(*[When(pk=pk, then=position) for position, pk in enumerate(result_ids)], output_field=IntegerField())
        return queryset.filter(pk__in=result_ids).order_by(relevance)

    def filter_queryset(self, queryset):
        search_term = (self.request.GET.get("search") or "").strip()
        for backend in list(self.filter_backends):
            if search_term and backend is filters.OrderingFilter and not self.request.GET.get("ordering"):
                continue
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PostCreateSerializer
        return PostSerializer

    def perform_create(self, serializer):
        post = serializer.save(author=self.request.user)
        invalidate_cache_keys("post_list:page:1:tag:all", "post_list:ids:tag:all")
        _invalidate_blog_public_views()
        for tag in post.tags.all():
            if tag.slug:
                invalidate_cache_keys(f"post_list:page:1:tag:{tag.slug}", f"post_list:ids:tag:{tag.slug}")
                invalidate_public_view_caches(
                    f"view:post_list:1:{tag.slug}:newest",
                    f"view:post_list:1:{tag.slug}:oldest",
                    f"view:post_list:1:{tag.slug}:title_az",
                    f"view:post_list:1:{tag.slug}:title_za",
                )


class PostDetailAPIView(RedirectAnonymousUsersToBlogMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.published.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrAdminOrReadOnly]

    def _invalidate_post_caches(self, post):
        invalidate_cache_keys("post_list:page:1:tag:all", "post_list:ids:tag:all")
        _invalidate_blog_public_views()
        for tag in post.tags.all():
            if tag.slug:
                invalidate_cache_keys(f"post_list:page:1:tag:{tag.slug}", f"post_list:ids:tag:{tag.slug}")
                invalidate_public_view_caches(
                    f"view:post_list:1:{tag.slug}:newest",
                    f"view:post_list:1:{tag.slug}:oldest",
                    f"view:post_list:1:{tag.slug}:title_az",
                    f"view:post_list:1:{tag.slug}:title_za",
                )

    def perform_update(self, serializer):
        post = serializer.save()
        self._invalidate_post_caches(post)

    def perform_destroy(self, instance):
        tags = list(instance.tags.all())
        instance.delete()
        invalidate_cache_keys("post_list:page:1:tag:all", "post_list:ids:tag:all")
        _invalidate_blog_public_views()
        for tag in tags:
            if tag.slug:
                invalidate_cache_keys(f"post_list:page:1:tag:{tag.slug}", f"post_list:ids:tag:{tag.slug}")
                invalidate_public_view_caches(
                    f"view:post_list:1:{tag.slug}:newest",
                    f"view:post_list:1:{tag.slug}:oldest",
                    f"view:post_list:1:{tag.slug}:title_az",
                    f"view:post_list:1:{tag.slug}:title_za",
                )


class CommentListAPIView(RedirectAnonymousUsersToBlogMixin, generics.ListCreateAPIView):
    pagination_class = StandardResultsSetPagination
    queryset = Comment.objects.filter(active=True).select_related('post', 'author')
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["post", "author__username", "active"]
    ordering_fields = ["created"]
    ordering = ["-created"]

    def get_queryset(self):
        queryset = super().get_queryset()
        search_term = (self.request.GET.get("search") or "").strip()
        if not search_term:
            return queryset
        result_ids = comment_search_result_ids(search_term)
        if not result_ids:
            return queryset.none()
        relevance = Case(*[When(pk=pk, then=position) for position, pk in enumerate(result_ids)], output_field=IntegerField())
        return queryset.filter(pk__in=result_ids).order_by(relevance)

    def filter_queryset(self, queryset):
        search_term = (self.request.GET.get("search") or "").strip()
        for backend in list(self.filter_backends):
            if search_term and backend is filters.OrderingFilter and not self.request.GET.get("ordering"):
                continue
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CommentWriteSerializer
        return CommentSerializer

    def perform_create(self, serializer):
        serializer.save()


class CommentDetailAPIView(RedirectAnonymousUsersToBlogMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.filter(active=True).select_related('post', 'author')
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrAdminOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in {"PUT", "PATCH"}:
            return CommentWriteSerializer
        return CommentSerializer


@api_view(["GET"])
def tag_list_api(request):
    tags = Tag.objects.all().order_by("name")
    serializer = TagSerializer(tags, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def tag_detail_api(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    serializer = TagSerializer(tag)
    return Response(serializer.data)
