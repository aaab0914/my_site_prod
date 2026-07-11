import logging
import time

from django.conf import settings

from blog.models import AuditLog


logger = logging.getLogger(__name__)

_SKIP_PREFIXES = (
    "/static/",
    "/media/",
    "/favicon.ico",
    "/robots.txt",
    "/sitemap.xml",
    "/metrics",
    "/celery-metrics/",
)


class AuditLoggingMiddleware:
    """Log only valuable requests to avoid extra database writes on routine page views."""

    def __init__(self, get_response):
        self.get_response = get_response
        admin_path = getattr(settings, "ADMIN_URL_PATH", "admin/").strip("/")
        self.always_log_prefixes = (
            f"/{admin_path}/",
            "/users/login/",
            "/users/logout/",
        )

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        response_time = time.time() - start_time

        if not self.should_log(request, response):
            return response

        ip = self.get_client_ip(request)

        try:
            AuditLog.objects.create(
                user=request.user
                if getattr(request.user, "is_authenticated", False) and getattr(request.user, "pk", None)
                else None,
                method=request.method,
                path=request.path,
                ip_address=ip,
                status_code=response.status_code,
                response_time=response_time,
            )
        except Exception as exc:
            logger.warning("Failed to write audit log: %s", exc)

        return response

    def should_log(self, request, response):
        path = request.path or "/"
        if path.startswith(_SKIP_PREFIXES):
            return False

        method = (request.method or "GET").upper()
        if method not in {"GET", "HEAD", "OPTIONS"}:
            return True

        if response.status_code >= 400:
            return True

        return path.startswith(self.always_log_prefixes)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR")
