from django_elasticsearch_dsl import Document, Index, fields
from django_elasticsearch_dsl.registries import registry

from .models import Post


posts_index = Index("posts")
posts_index.settings(number_of_shards=1, number_of_replicas=0)


@registry.register_document
class PostDocument(Document):
    author = fields.ObjectField(
        properties={
            "username": fields.KeywordField(),
        }
    )

    class Index:
        name = "posts"

    class Django:
        model = Post
        fields = [
            "title",
            "slug",
            "publish",
            "status",
        ]
