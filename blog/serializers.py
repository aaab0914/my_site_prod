"""
Serializers for the blog application's REST API.

This module defines how Django model instances are converted to and from
JSON representations for the blog's API endpoints. It handles nested
relationships and custom field mappings for posts, comments, and tags.
"""

# =============================================================================
# IMPORTS (All imports moved to the top)
# =============================================================================

from rest_framework import serializers
# serializers: Django REST Framework's serialization module.
# Provides ModelSerializer and field types for converting models to/from JSON.

from .models import Post, Comment
# Post: The main blog post model.
# Comment: User comments attached to posts.

from taggit.models import Tag


# Tag: Model from django-taggit representing a single tag.


# =============================================================================
# SERIALIZER: TAG
# =============================================================================

class TagSerializer(serializers.ModelSerializer):
    """
    Serializer for Tag model instances.
    Provides a simple representation of a tag with its ID, name, and slug.
    """

    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']
        # fields: The model fields to include in the JSON representation.


# =============================================================================
# SERIALIZER: COMMENT
# =============================================================================

class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for Comment model instances.
    Includes a custom 'name' field that resolves to the comment author's
    display name (username or email prefix).
    """
    name = serializers.SerializerMethodField()

    # name: A custom read-only field that delegates to the get_name method.

    class Meta:
        model = Comment
        fields = ['id', 'name', 'body', 'created']
        read_only_fields = ['created']
        # read_only_fields: These fields cannot be modified via API requests.

    def get_name(self, obj):
        """
        Return the display name for the comment author.

        Args:
            obj: A Comment model instance.

        Returns:
            str: The author's username or email prefix.
        """
        return obj.display_name


# =============================================================================
# SERIALIZER: POST (READ-ONLY / FULL DETAILS)
# =============================================================================

class PostSerializer(serializers.ModelSerializer):
    """
    Serializer for Post model instances.
    Provides a complete representation including nested tags, author,
    and comments. This is used for GET requests (reading posts).
    """
    tags = TagSerializer(many=True, read_only=True)
    # tags: Nested serializer for all tags associated with the post.

    author = serializers.StringRelatedField(read_only=True)
    # author: String representation of the author (username).

    comments = CommentSerializer(many=True, read_only=True)

    # comments: Nested serializer for all comments on the post.

    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'body', 'author',
            'publish', 'created', 'updated', 'status',
            'tags', 'comments', 'cover_image'
        ]
        read_only_fields = ['created', 'updated', 'publish']
        # read_only_fields: Timestamps that cannot be modified via API.


# =============================================================================
# SERIALIZER: POST (CREATE / WRITE-ONLY)
# =============================================================================

class PostCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new Post instances.
    Accepts tags as a simple list of strings and handles tag association
    during post creation.
    """
    tags = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False
    )

    # tags: A write-only field that accepts a list of tag name strings.
    # child: Each element in the list must be a string (tag name).

    class Meta:
        model = Post
        fields = ['title', 'slug', 'body', 'status', 'tags']
        # fields: Fields required/optional for creating a new post.

    def create(self, validated_data):
        """
        Create a new Post instance and associate any provided tags.

        Args:
            validated_data: Dictionary of cleaned field data from the request.

        Returns:
            Post: The newly created Post instance.
        """
        # Pop tags from validated_data to handle them separately.
        tags = validated_data.pop('tags', [])
        # Create the post instance with the remaining validated data.
        post = Post.objects.create(**validated_data)
        # Add any provided tags to the newly created post.
        if tags:
            post.tags.add(*tags)
        return post

# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                        blog/serializers.py                                 │
# │                    (REST API Serializers)                                  │
# └─────────────────────────────────────────────────────────────────────────────┘
#                                       │
#                                       ▼
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                            IMPORTS (Dependencies)                           │
# ├─────────────────────────────────────────────────────────────────────────────┤
# │  rest_framework            │  .models                                     │
# │  └─ serializers            │  ├─ Post                                     │
# │  taggit.models             │  └─ Comment                                  │
# │  └─ Tag                    │                                             │
# └─────────────────────────────────────────────────────────────────────────────┘
#                                       │
#                                       ▼
#                  ┌────────────────────────────────────────────────┐
#                  │            Serializer Classes                  │
#                  └────────────────────────────────────────────────┘
#                                       │
#          ┌────────────────────────────┼────────────────────────────┐
#          ▼                            ▼                            ▼
# ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
# │   TagSerializer      │  │   CommentSerializer   │  │   PostSerializer     │
# │   (Class)            │  │   (Class)            │  │   (Class)            │
# ├──────────────────────┤  ├──────────────────────┤  ├──────────────────────┤
# │ Inherits:            │  │ Inherits:            │  │ Inherits:            │
# │   serializers.       │  │   serializers.       │  │   serializers.       │
# │   ModelSerializer    │  │   ModelSerializer    │  │   ModelSerializer    │
# │                      │  │                      │  │                      │
# │ Model:               │  │ Model:               │  │ Model:               │
# │   Tag                │  │   Comment            │  │   Post               │
# │                      │  │                      │  │                      │
# │ Fields:              │  │ Custom Fields:       │  │ Nested Fields:       │
# │   id                 │  │   name (Serializer  │  │   tags (TagSerializer)│
# │   name               │  │   MethodField)       │  │   author (String)    │
# │   slug               │  │                      │  │   comments (Comment) │
# │                      │  │ Custom Method:       │  │                      │
# │                      │  │   get_name()         │  │ Read Only:           │
# │                      │  │                      │  │   created, updated,  │
# │                      │  │ Read Only:           │  │   publish            │
# │                      │  │   created            │  │                      │
# └──────────────────────┘  └──────────────────────┘  └──────────────────────┘
#                                       │
#                                       ▼
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                           PostCreateSerializer                              │
# │                              (Class)                                        │
# ├─────────────────────────────────────────────────────────────────────────────┤
# │  Inherits: serializers.ModelSerializer                                     │
# │  Model: Post                                                               │
# │                                                                             │
# │  Custom Fields:                                                             │
# │    - tags: ListField(child=CharField(), write_only=True)                   │
# │                                                                             │
# │  Fields: title, slug, body, status, tags                                   │
# │                                                                             │
# │  Custom Logic:                                                              │
# │    - create(): Populates tags from the list and adds them to the post.      │
# │                                                                             │
# │  Purpose:                                                                   │
# │    This serializer is used exclusively for POST requests (creating posts).  │
# │    It handles tag strings from the request and associates them correctly.   │
# └─────────────────────────────────────────────────────────────────────────────┘