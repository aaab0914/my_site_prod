from datetime import timedelta
from pathlib import Path

from django.conf import settings
from celery import shared_task
from django.utils import timezone

from blog.models import AuditLog
from my_site.logging_policy import ensure_runtime_log_heartbeats, purge_runtime_logs


@shared_task
def sync_site_media_task():
    return {
        "enabled": False,
        "reason": "Automatic media sync is disabled. Media files move to .trash only when users delete objects in the site UI.",
    }


@shared_task
def purge_old_audit_logs_task(days=90):
    cutoff = timezone.now() - timedelta(days=days)
    deleted_count, _ = AuditLog.objects.filter(timestamp__lt=cutoff).delete()
    return deleted_count


@shared_task
def purge_old_runtime_logs_task(days=30):
    log_root = Path(settings.BASE_DIR) / "logs"
    heartbeat_result = ensure_runtime_log_heartbeats(log_root)
    purge_result = purge_runtime_logs(log_root, retention_days=days)
    purge_result["heartbeats"] = heartbeat_result
    return purge_result
