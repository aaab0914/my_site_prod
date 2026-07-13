from django.core.cache import cache
from django.http import HttpResponse
from django.template.response import TemplateResponse


SITE_HTML_CACHE_TTL = 60 * 60 * 24 * 30


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


def site_index(request):
    return render_public_cached_template(request, "view:site_index", "index.html", timeout=300)
