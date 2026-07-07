"""
Elasticsearch document definitions for the blog application.

This module defines how Post model instances are indexed and stored in
Elasticsearch, enabling full-text search capabilities across the blog.
"""

# =============================================================================
# IMPORTS
# =============================================================================

from django_elasticsearch_dsl import Document, Index, fields
# Document: Base class for defining an Elasticsearch document mapping.
# Index: Represents an Elasticsearch index and its settings.
# fields: Field types for defining document properties (e.g., ObjectField, KeywordField).

from django_elasticsearch_dsl.registries import registry
# registry: A global registry that tracks registered document classes.
# Automatically manages index creation and updates.

from .models import Post
# Post: The Django model representing blog posts.
# This is the model that will be indexed in Elasticsearch.


# =============================================================================
# INDEX DEFINITION
# =============================================================================

posts_index = Index("posts")
# Initialize an Elasticsearch index named "posts".
# This index will store documents representing individual blog posts.

posts_index.settings(number_of_shards=1, number_of_replicas=0)
# Configure the index settings:
# - number_of_shards=1: Use a single shard for this index.
# - number_of_replicas=0: No replica shards (suitable for development/testing).


# =============================================================================
# DOCUMENT CLASS
# =============================================================================

@registry.register_document
class PostDocument(Document):
    """
    Elasticsearch document mapping for the Post model.

    Defines how Post instances are serialized and stored in Elasticsearch.
    Includes a custom field for the author information.
    """
    author = fields.ObjectField(
        properties={
            "username": fields.KeywordField(),
        }
    )
    # author: A nested object field that stores the author's username.
    # This field type allows Elasticsearch to search and filter by author username.
    # ObjectField: Stores a JSON object containing sub-fields.
    # KeywordField: Stores a string that is not analyzed (exact match search).

    class Index:
        # Inner class defining the Elasticsearch index name.
        name = "posts"

    class Django:
        # Inner class defining the Django model and fields to be indexed.
        model = Post
        # The Django model that this document represents.

        fields = [
            "title",
            "slug",
            "publish",
            "status",
        ]
        # The list of model fields to be automatically indexed.
        # Each field in this list will be stored as a corresponding Elasticsearch field.

# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                       blog/documents.py                                    │
# │              (Elasticsearch Document Definitions)                          │
# └─────────────────────────────────────────────────────────────────────────────┘
#                                       │
#                                       ▼
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                            IMPORTS (Dependencies)                           │
# ├─────────────────────────────────────────────────────────────────────────────┤
# │  django_elasticsearch_dsl    │  django_elasticsearch_dsl.registries        │
# │  ├─ Document                 │  └─ registry                                │
# │  ├─ Index                    │  ..models                                   │
# │  ├─ fields                   │  └─ Post                                    │
# │  │   ├─ ObjectField          │                                             │
# │  │   └─ KeywordField         │                                             │
# └─────────────────────────────────────────────────────────────────────────────┘
#                                       │
#                                       ▼
#                  ┌────────────────────────────────────────────────┐
#                  │          Definitions & Classes                 │
#                  └────────────────────────────────────────────────┘
#                                       │
#          ┌────────────────────────────┼────────────────────────────┐
#          ▼                            ▼                            ▼
# ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
# │   posts_index        │  │   PostDocument       │  │   PostDocument.Index │
# │   (Variable)         │  │   (Class)            │  │   (Inner Class)      │
# ├──────────────────────┤  ├──────────────────────┤  ├──────────────────────┤
# │ Purpose:             │  │ Inherits:            │  │ Purpose:             │
# │   Define the main    │  │   Document           │  │   Define the         │
# │   Elasticsearch      │  │                      │  │   Elasticsearch      │
# │   index name         │  │ Decorators:          │  │   index name         │
# │                      │  │   @registry.register │  │                      │
# │                     │  │   _document           │  │   Value:             │
# │ Configuration:      │  │                      │  │   "posts"            │
# │   number_of_shards=1│  │ Purpose:             │  │                      │
# │   number_of_replicas│  │   Map Post model to  │  │                      │
# │   =0                │  │   Elasticsearch      │  │                      │
# │                      │  │                      │  │                      │
# │                      │  │ Custom Fields:       │  │                      │
# │                      │  │   author (ObjectField│  │                      │
# │                      │  │   -> username)       │  │                      │
# └──────────────────────┘  └──────────────────────┘  └──────────────────────┘
#                                       │
#                                       ▼
# ┌─────────────────────────────────────────────────────────────────────────────┐
# │                       PostDocument.Django (Inner Class)                      │
# ├─────────────────────────────────────────────────────────────────────────────┤
# │  Purpose: Bind the document class to a Django model and specify fields.     │
# │                                                                             │
# │  Attributes:                                                                │
# │    - model: Post                                                           │
# │    - fields: ["title", "slug", "publish", "status"]                        │
# │                                                                             │
# │  How it works:                                                             │
# │    The Django inner class tells the library which Django model to use       │
# │    and which fields to automatically index.                                │
# └─────────────────────────────────────────────────────────────────────────────┘