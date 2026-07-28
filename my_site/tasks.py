from datetime import timedelta, timezone as dt_timezone
from pathlib import Path

from django.conf import settings
from celery import shared_task
from django.utils import timezone

from blog.models import AuditLog


LOG_FILE_PREFIXES = {
    "django": "django",
    "django-error": "django-error",
    "celery": "celery",
    "gunicorn-access": "gunicorn-access",
    "gunicorn-error": "gunicorn-error",
    "nginx-access": "nginx-access",
    "nginx-error": "nginx-error",
    "backup": "backup",
}


def ensure_daily_runtime_logs():
    log_root = Path(settings.BASE_DIR) / "logs"
    now = timezone.localtime()
    month_dir = now.strftime("%Y-%m")
    day = now.strftime("%Y-%m-%d")
    created = []

    for log_type, prefix in LOG_FILE_PREFIXES.items():
        target_dir = log_root / log_type / month_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / f"{prefix}-{day}.log"
        if not target_file.exists():
            target_file.touch()
            created.append(str(target_file))

    return {
        "log_root": str(log_root),
        "created": created,
        "ensured": [str((log_root / log_type / month_dir / f"{prefix}-{day}.log")) for log_type, prefix in LOG_FILE_PREFIXES.items()],
    }


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

    month_dirs = sorted((path for path in log_root.rglob("*") if path.is_dir()), reverse=True)
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


@shared_task
def ensure_daily_runtime_logs_task():
    return ensure_daily_runtime_logs()
