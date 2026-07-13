from datetime import timedelta, timezone as dt_timezone
from pathlib import Path

from django.conf import settings
from celery import shared_task
from django.utils import timezone

from blog.models import AuditLog


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
    if not log_root.exists():
        return {"deleted_files": 0, "deleted_dirs": 0, "log_root": str(log_root)}

    cutoff = timezone.now() - timedelta(days=days)
    deleted_files = 0
    deleted_dirs = 0

    for file_path in log_root.rglob("*.log"):
        try:
            modified = timezone.datetime.fromtimestamp(file_path.stat().st_mtime, tz=dt_timezone.utc)
        except FileNotFoundError:
            continue
        if modified >= cutoff:
            continue
        file_path.unlink(missing_ok=True)
        deleted_files += 1

    month_dirs = sorted((path for path in log_root.iterdir() if path.is_dir()), reverse=True)
    for directory in month_dirs:
        try:
            next(directory.iterdir())
        except StopIteration:
            directory.rmdir()
            deleted_dirs += 1
        except FileNotFoundError:
            continue

    return {
        "deleted_files": deleted_files,
        "deleted_dirs": deleted_dirs,
        "log_root": str(log_root),
    }
