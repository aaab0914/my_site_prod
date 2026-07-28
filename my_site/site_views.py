from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse

from blog.search import elasticsearch_is_available, get_es_client, search_result_ids


SITE_HTML_CACHE_TTL = 60 * 60 * 24 * 30


def require_authenticated_blog_redirect(request):
    if request.user.is_authenticated:
        return None
    return redirect("blog:all_posts_list")


def render_public_cached_template(request, cache_key, template_name, context=None, timeout=SITE_HTML_CACHE_TTL):
    context = context or {}
    if request.method != "GET" or request.user.is_authenticated:
        return TemplateResponse(request, template_name, context)

    cached_payload = cache.get(cache_key)
    if cached_payload is not None:
        response = HttpResponse(cached_payload["content"], content_type=cached_payload["content_type"])
        response["X-View-Cache"] = "HIT"
        return response

    response = TemplateResponse(request, template_name, context)
    response.render()
    cache.set(
        cache_key,
        {"content": response.content, "content_type": response.get("Content-Type", "text/html; charset=utf-8")},
        timeout,
    )
    response["X-View-Cache"] = "MISS"
    return response


def queue_operation_success(
    request,
    *,
    title,
    message,
    primary_label,
    primary_url,
    secondary_label=None,
    secondary_url=None,
):
    request.session["operation_success"] = {
        "title": str(title),
        "message": str(message),
        "primary_label": str(primary_label),
        "primary_url": str(primary_url),
        "secondary_label": str(secondary_label) if secondary_label is not None else None,
        "secondary_url": str(secondary_url) if secondary_url is not None else None,
    }
    return redirect("operation_success")


def site_index(request):
    return render_public_cached_template(request, "view:site_index", "index.html", timeout=300)


def api_guide(request):
    auth_redirect = require_authenticated_blog_redirect(request)
    if auth_redirect is not None:
        return auth_redirect
    return TemplateResponse(request, "api_guide.html", {})


def api_python_guide(request):
    auth_redirect = require_authenticated_blog_redirect(request)
    if auth_redirect is not None:
        return auth_redirect
    return TemplateResponse(request, "api_python_guide.html", {})


def api_endpoints(request):
    auth_redirect = require_authenticated_blog_redirect(request)
    if auth_redirect is not None:
        return auth_redirect
    return TemplateResponse(request, "api_endpoints.html", {})


def operation_success(request):
    payload = request.session.pop("operation_success", None)
    if not payload:
        return redirect("site_index")
    response = TemplateResponse(request, "operation_success.html", payload)
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, private"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    response["Vary"] = "Cookie"
    return response



def search_status(request):
    client = get_es_client()
    ping = bool(client.ping())
    index_exists = bool(client.indices.exists(index="posts")) if ping else False
    document_count = client.count(index="posts").get("count", 0) if index_exists else 0
    health = client.cluster.health(index="posts").get("status", "down") if index_exists else "down"
    sample_query = "python"
    sample_ids, sample_backend = search_result_ids(sample_query)
    context = {
        "ping": ping,
        "available": elasticsearch_is_available(force=True),
        "index_exists": index_exists,
        "document_count": document_count,
        "health": health,
        "sample_query": sample_query,
        "sample_backend": sample_backend,
        "sample_ids": sample_ids[:20],
        "sample_count": len(sample_ids),
    }
    return render_public_cached_template(request, "view:search_status", "search_status.html", context, timeout=120)
