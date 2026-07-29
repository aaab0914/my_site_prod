from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse


SITE_HTML_CACHE_TTL = 60 * 60 * 24 * 30  # 30 days


def health_check(request):
    """
    Lightweight health check endpoint for Docker container probes.
    Returns 200 OK when the application is responsive.
    """
    return HttpResponse("ok", content_type="text/plain", status=200)


def render_public_cached_template(request, cache_key, template_name, context=None, timeout=SITE_HTML_CACHE_TTL):
    context = context or {}
    if request.method != "GET" or request.user.is_authenticated or settings.DEBUG:
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
    return render_public_cached_template(request, "view:site_index", "index.html", timeout=SITE_HTML_CACHE_TTL)


def queue_operation_success(request, *, title, message, primary_label, primary_url, secondary_label="Blog Home", secondary_url=None):
    request.session["operation_success"] = {
        "title": str(title),
        "message": str(message),
        "primary_label": str(primary_label),
        "primary_url": str(primary_url),
        "secondary_label": str(secondary_label),
        "secondary_url": str(secondary_url or reverse("blog:all_posts_list")),
    }
    return redirect("operation_success")


def operation_success(request):
    payload = request.session.pop("operation_success", None)
    if not payload:
        return redirect("site_index")
    return TemplateResponse(request, "operation_success.html", payload)
