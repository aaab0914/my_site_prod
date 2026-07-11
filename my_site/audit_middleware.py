import time
import logging
from blog.models import AuditLog


logger = logging.getLogger(__name__)


class AuditLoggingMiddleware:
    """记录所有请求和响应的中间件"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        response_time = time.time() - start_time

        # 获取客户端IP
        ip = self.get_client_ip(request)

        # 记录请求
        try:
            AuditLog.objects.create(
                user=request.user
                if getattr(request.user, "is_authenticated", False) and getattr(request.user, "pk", None)
                else None,
                method=request.method,
                path=request.path,
                ip_address=ip,
                status_code=response.status_code,
                response_time=response_time
            )
        except Exception as exc:
            logger.warning("Failed to write audit log: %s", exc)

        return response

    def get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
