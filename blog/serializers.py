"""
Serializers for the blog application's REST API.

This module defines how Django model instances are converted to and from
JSON representations for the blog's API endpoints. It handles nested
relationships and custom field mappings for posts, comments, and tags.
"""

from rest_framework import serializers
from .models import Post, Comment
from my_site.tagging import normalize_tag_list
from taggit.models import Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class CommentSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    author = serializers.StringRelatedField(read_only=True)
    post_title = serializers.CharField(source='post.title', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'post', 'post_title', 'author', 'name', 'body', 'created', 'active']
        read_only_fields = ['created', 'author', 'name', 'post_title']

    def get_name(self, obj):
        return obj.display_name


class CommentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['post', 'body', 'active']
        extra_kwargs = {
            'active': {'required': False},
        }

    def validate_active(self, value):
        request = self.context.get('request')
        if request and not request.user.is_staff and not request.user.is_superuser:
            return True
        return value

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        email = getattr(user, 'email', '') or f'{user.username}@local.invalid'
        validated_data['author'] = user
        validated_data['email'] = email
        validated_data['active'] = validated_data.get('active', True)
        return Comment.objects.create(**validated_data)

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if request and not request.user.is_staff and not request.user.is_superuser:
            validated_data.pop('active', None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance


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

    def validate_tags(self, value):
        return normalize_tag_list(value)

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        post = Post.objects.create(**validated_data)
        if tags:
            post.tags.set(tags)
        return post
