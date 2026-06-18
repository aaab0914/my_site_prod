from rest_framework import generics, permissions, filters
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Post, Comment
from .serializers import PostSerializer, PostCreateSerializer, CommentSerializer
from django.shortcuts import get_object_or_404


class PostListAPIView(generics.ListCreateAPIView):
    queryset = Post.published.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'author__username', 'tags__name']
    search_fields = ['title', 'body']
    ordering_fields = ['publish', 'title']
    ordering = ['-publish']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PostCreateSerializer
        return PostSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.published.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return Post.objects.filter(author=self.request.user)
        return Post.published.all()


class CommentListAPIView(generics.ListCreateAPIView):
    queryset = Comment.objects.filter(active=True)
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['post', 'name', 'active']

    def perform_create(self, serializer):
        serializer.save()


class CommentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return Comment.objects.filter(name=self.request.user.username)
        return Comment.objects.filter(active=True)


@api_view(['GET'])
def tag_list_api(request):
    from taggit.models import Tag
    tags = Tag.objects.all().order_by('name')
    serializer = TagSerializer(tags, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def tag_detail_api(request, slug):
    from taggit.models import Tag
    tag = get_object_or_404(Tag, slug=slug)
    serializer = TagSerializer(tag)
    return Response(serializer.data)