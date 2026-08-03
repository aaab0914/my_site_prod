from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
import shutil
import re

from django.utils import timezone


@dataclass(frozen=True)
class RuntimeLogTarget:
    key: str
    label: str
    prefix: str


RUNTIME_LOG_RETENTION_DAYS = 120
RUNTIME_LOG_TARGETS = (
    RuntimeLogTarget("celery", "Celery", "celery"),
    RuntimeLogTarget("nginx", "Nginx", "nginx"),
    RuntimeLogTarget("gunicorn_access", "Gunicorn Access", "gunicorn-access"),
    RuntimeLogTarget("gunicorn_error", "Gunicorn Error", "gunicorn-error"),
    RuntimeLogTarget("django", "Django", "django"),
    RuntimeLogTarget("django_error", "Django Error", "error"),
)
MANAGED_MONTH_DIR_RE = re.compile(r"^\d{4}-\d{2}$")
MANAGED_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def runtime_log_path(log_root, target, when=None):
    current = when or timezone.localtime()
    log_root = Path(log_root)
    month_dir = log_root / current.strftime("%Y-%m")
    return month_dir / f"{target.prefix}-{current.strftime('%Y-%m-%d')}.log"


def is_managed_runtime_log(file_path, log_root):
    file_path = Path(file_path)
    log_root = Path(log_root)
    try:
        relative_path = file_path.relative_to(log_root)
    except ValueError:
        return False

    if len(relative_path.parts) != 2:
        return False
    month_dir, filename = relative_path.parts
    if not MANAGED_MONTH_DIR_RE.fullmatch(month_dir):
        return False
    if file_path.suffix != ".log":
        return False

    stem = file_path.stem
    for target in RUNTIME_LOG_TARGETS:
        prefix = f"{target.prefix}-"
        if not stem.startswith(prefix):
            continue
        date_part = stem[len(prefix):]
        return bool(MANAGED_DATE_RE.fullmatch(date_part))
    return False


def ensure_runtime_log_heartbeats(log_root, when=None):
    current = when or timezone.localtime()
    results = []
    for target in RUNTIME_LOG_TARGETS:
        path = runtime_log_path(log_root, target, current)
        path.parent.mkdir(parents=True, exist_ok=True)
        created = not path.exists() or path.stat().st_size == 0
        if created:
            timestamp = current.strftime("%Y-%m-%d %H:%M:%S")
            path.write_text(f"[{timestamp}] heartbeat: no new {target.label} log entries yet.\n", encoding="utf-8")
        results.append({"key": target.key, "path": str(path), "created": created})
    return results


def purge_runtime_logs(log_root, retention_days=RUNTIME_LOG_RETENTION_DAYS, when=None):
    current = when or timezone.localtime()
    cutoff = current - timedelta(days=retention_days)
    log_root = Path(log_root)
    trash_root = log_root.parent / ".trash" / "logs" / current.strftime("%Y%m%d_%H%M%S")
    trashed_files = 0
    deleted_dirs = 0

    if not log_root.exists():
        return {"trashed_files": 0, "deleted_dirs": 0, "log_root": str(log_root), "trash_root": str(trash_root)}

    for file_path in log_root.rglob("*.log"):
        if not is_managed_runtime_log(file_path, log_root):
            continue
        try:
            modified = timezone.datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.get_current_timezone())
        except FileNotFoundError:
            continue
        if modified >= cutoff:
            continue
        try:
            relative_path = file_path.relative_to(log_root)
        except ValueError:
            continue
        target_path = trash_root / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(file_path), str(target_path))
        trashed_files += 1

    for directory in sorted((path for path in log_root.iterdir() if path.is_dir()), reverse=True):
        try:
            next(directory.iterdir())
        except StopIteration:
            directory.rmdir()
            deleted_dirs += 1
        except FileNotFoundError:
            continue

    return {"trashed_files": trashed_files, "deleted_dirs": deleted_dirs, "log_root": str(log_root), "trash_root": str(trash_root)}
