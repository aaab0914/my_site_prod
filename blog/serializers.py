from rest_framework import serializers
from .models import Post, Comment
from taggit.models import Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class CommentSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'name', 'email', 'body', 'created', 'active']
        read_only_fields = ['created']

    def get_name(self, obj):
        return obj.display_name


class PostSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = serializers.StringRelatedField(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'body', 'author',
            'publish', 'created', 'updated', 'status',
            'tags', 'comments', 'cover_image'
        ]
        read_only_fields = ['created', 'updated', 'publish']


class PostCreateSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Post
        fields = ['title', 'slug', 'body', 'status', 'tags']

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        post = Post.objects.create(**validated_data)
        if tags:
            post.tags.add(*tags)
        return post
