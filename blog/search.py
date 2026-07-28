"""Search helpers with Elasticsearch-first lookup and database fallback."""

import logging

from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity
from django.core.cache import cache
from django.db.models import Case, IntegerField, When
from elasticsearch import Elasticsearch

from .models import Comment, Post

logger = logging.getLogger(__name__)

SEARCH_CACHE_TTL = 60 * 60 * 24 * 30
STATUS_CACHE_TTL = 300
SEARCH_RESULT_LIMIT = 250


def get_es_client():
    hosts = settings.ELASTICSEARCH_DSL["default"]["hosts"]
    return Elasticsearch(hosts)


def elasticsearch_is_available(force=False):
    cache_key = "search:elasticsearch:available"
    if not force:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
    try:
        available = bool(get_es_client().ping())
    except Exception:
        logger.exception("Elasticsearch health check failed")
        available = False
    cache.set(cache_key, available, STATUS_CACHE_TTL)
    return available


def db_search_result_ids(query):
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
        total_similarity=(TrigramSimilarity("title", normalized_query) * 2 + TrigramSimilarity("body", normalized_query)),
    )
    trigram_results = trigram_base.filter(title_similarity__gt=0.1) | trigram_base.filter(body_similarity__gt=0.1)

    combined_results = (full_text_results | trigram_results.order_by("-total_similarity", "-publish")).distinct()
    return list(
        combined_results.annotate(
            final_rank=SearchRank(search_vector, search_query) + (TrigramSimilarity("title", normalized_query) * 2)
        ).order_by("-final_rank", "-publish").values_list("id", flat=True)
    )


def es_search_result_ids(query, limit=SEARCH_RESULT_LIMIT):
    normalized_query = (query or "").strip()
    if not normalized_query:
        return []

    body = {
        "size": limit,
        "query": {
            "bool": {
                "filter": [{"term": {"status": "pb"}}],
                "should": [
                    {"match_phrase": {"title": {"query": normalized_query, "boost": 20}}},
                    {"match": {"title": {"query": normalized_query, "boost": 12}}},
                    {"match_phrase": {"tags": {"query": normalized_query, "boost": 14}}},
                    {
                        "multi_match": {
                            "query": normalized_query,
                            "fields": ["title^10", "tags^8", "slug^6", "body^2", "author.username^2"],
                            "type": "best_fields",
                            "fuzziness": "AUTO",
                        }
                    },
                    {
                        "multi_match": {
                            "query": normalized_query,
                            "fields": ["title^16", "body^3"],
                            "type": "phrase",
                            "boost": 3,
                        }
                    },
                ],
                "minimum_should_match": 1,
            }
        },
        "sort": ["_score", {"publish": {"order": "desc"}}],
        "_source": False,
    }
    response = get_es_client().search(index="posts", body=body)
    hits = response.get("hits", {}).get("hits", [])
    result_ids = []
    for hit in hits:
        pk = hit.get("_id")
        try:
            result_ids.append(int(pk))
        except (TypeError, ValueError):
            logger.warning("Skipping non-integer Elasticsearch hit id: %r", pk)
    return result_ids


def search_result_ids(query):
    normalized_query = (query or "").strip()
    if not normalized_query:
        return [], "empty"

    cache_key = f"post_search:query:{normalized_query.lower()}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached, "cache"

    backend = "database"
    result_ids = []
    if elasticsearch_is_available():
        try:
            result_ids = es_search_result_ids(normalized_query)
            backend = "elasticsearch"
        except Exception:
            logger.exception("Elasticsearch query failed; falling back to database search")

    if not result_ids:
        result_ids = db_search_result_ids(normalized_query)
        backend = "database" if backend != "elasticsearch" else "database-fallback"

    cache.set(cache_key, result_ids, SEARCH_CACHE_TTL)
    return result_ids, backend


def cached_search_result_ids(query):
    return search_result_ids(query)[0]


def ordered_posts_from_ids(post_ids, queryset=None):
    if not post_ids:
        return Post.published.none()
    queryset = queryset or Post.published.all()
    ordering = Case(*[When(pk=pk, then=position) for position, pk in enumerate(post_ids)], output_field=IntegerField())
    return queryset.filter(pk__in=post_ids).order_by(ordering)


def invalidate_search_caches():
    cache.delete("search:elasticsearch:available")


def comment_search_result_ids(query, limit=SEARCH_RESULT_LIMIT):
    normalized_query = (query or "").strip()
    if not normalized_query:
        return []

    post_ids, _backend = search_result_ids(normalized_query)
    queryset = Comment.objects.filter(active=True).select_related("post", "author")
    if post_ids:
        queryset = queryset.filter(post_id__in=post_ids) | Comment.objects.filter(active=True, body__icontains=normalized_query).select_related("post", "author")
    else:
        queryset = queryset.filter(body__icontains=normalized_query)
    ordered = list(queryset.distinct().order_by("-created").values_list("id", flat=True)[:limit])
    return ordered
