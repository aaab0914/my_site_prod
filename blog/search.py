"""PostgreSQL-based search helpers.

Previously used Elasticsearch-first lookup with database fallback.
Elasticsearch has been removed in favor of PostgreSQL full-text search
(SearchVector + SearchRank) combined with trigram similarity for fuzzy
matching.
"""

import logging

from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    SearchVector,
    TrigramSimilarity,
)
from django.core.cache import cache
from django.db.models import Case, IntegerField, When

from .models import Comment, Post

logger = logging.getLogger(__name__)

SEARCH_CACHE_TTL = 60 * 60 * 24 * 30
SEARCH_RESULT_LIMIT = 250


def db_search_result_ids(query):
    """Return post IDs matching *query* using PostgreSQL full-text search + trigram."""
    normalized_query = (query or "").strip()
    if not normalized_query:
        return []

    search_vector = SearchVector("title", weight="A") + SearchVector("body", weight="B")
    search_query = SearchQuery(normalized_query)

    full_text_results = (
        Post.published.annotate(rank=SearchRank(search_vector, search_query))
        .filter(rank__gte=0.1)
        .order_by("-rank", "-publish")
    )

    trigram_base = Post.published.annotate(
        title_similarity=TrigramSimilarity("title", normalized_query),
        body_similarity=TrigramSimilarity("body", normalized_query),
        total_similarity=(
            TrigramSimilarity("title", normalized_query) * 2
            + TrigramSimilarity("body", normalized_query)
        ),
    )
    trigram_results = trigram_base.filter(
        title_similarity__gt=0.1
    ) | trigram_base.filter(body_similarity__gt=0.1)

    combined_results = (
        full_text_results | trigram_results.order_by("-total_similarity", "-publish")
    ).distinct()

    return list(
        combined_results.annotate(
            final_rank=SearchRank(search_vector, search_query)
            + (TrigramSimilarity("title", normalized_query) * 2)
        )
        .order_by("-final_rank", "-publish")
        .values_list("id", flat=True)
    )


def search_result_ids(query):
    """Return (list_of_post_ids, backend_name) for *query*.

    backend_name is always "database" now that Elasticsearch has been removed.
    """
    normalized_query = (query or "").strip()
    if not normalized_query:
        return [], "empty"

    cache_key = f"post_search:query:{normalized_query.lower()}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached, "cache"

    result_ids = db_search_result_ids(normalized_query)
    cache.set(cache_key, result_ids, SEARCH_CACHE_TTL)
    return result_ids, "database"


def cached_search_result_ids(query):
    return search_result_ids(query)[0]


def ordered_posts_from_ids(post_ids, queryset=None):
    if not post_ids:
        return Post.published.none()
    queryset = queryset or Post.published.all()
    ordering = Case(
        *[When(pk=pk, then=position) for position, pk in enumerate(post_ids)],
        output_field=IntegerField(),
    )
    return queryset.filter(pk__in=post_ids).order_by(ordering)


def invalidate_search_caches():
    """Clear search result cache."""
    try:
        cache.delete_pattern("post_search:*")
    except AttributeError:
        pass


def comment_search_result_ids(query, limit=SEARCH_RESULT_LIMIT):
    normalized_query = (query or "").strip()
    if not normalized_query:
        return []

    post_ids, _backend = search_result_ids(normalized_query)
    queryset = Comment.objects.filter(active=True).select_related("post", "author")
    if post_ids:
        queryset = queryset.filter(post_id__in=post_ids) | Comment.objects.filter(
            active=True, body__icontains=normalized_query
        ).select_related("post", "author")
    else:
        queryset = queryset.filter(body__icontains=normalized_query)
    ordered = list(
        queryset.distinct().order_by("-created").values_list("id", flat=True)[:limit]
    )
    return ordered