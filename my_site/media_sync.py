from pathlib import Path
import threading
import time

from django.apps import apps
from django.conf import settings
from django.db.models import FileField

_SYNC_LOCK = threading.Lock()
_LAST_SYNC_AT = 0.0
_PROTECTED_PREFIXES = ("audio/",)


def _disabled_sync_result():
    return {
        "enabled": False,
        "reason": "Automatic media sync is disabled. Media files move to .trash only when users delete objects in the site UI.",
        "missing_actions": [],
        "trashed_files": [],
        "deleted_records": 0,
        "cleared_fields": 0,
        "gallery_sync": {
            "missing_records": 0,
            "created_records": 0,
            "missing_record_ids": [],
            "deleted_records": 0,
            "cleared_fields": 0,
            "trashed_files": [],
            "missing_actions": [],
            "orphaned_files": [],
        },
    }


def _iter_file_fields():
    for model in apps.get_models():
        for field in model._meta.get_fields():
            if isinstance(field, FileField):
                yield model, field


def _is_protected_media(relative_name):
    normalized = (relative_name or "").replace("\\", "/").strip("/")
    return any(normalized.startswith(prefix) for prefix in _PROTECTED_PREFIXES)


def _handle_missing_file(instance, field):
    field_file = getattr(instance, field.name)
    relative_name = (field_file.name or "").replace("\\", "/").strip("/")
    if not relative_name:
        return None

    if _is_protected_media(relative_name):
        return {
            "type": "protected_missing_file_skipped",
            "model": instance._meta.label,
            "id": instance.pk,
            "field": field.name,
            "path": relative_name,
        }

    return {
        "type": "missing_file_detected_no_delete",
        "model": instance._meta.label,
        "id": instance.pk,
        "field": field.name,
        "path": relative_name,
    }


def sync_site_media():
    if not getattr(settings, "MEDIA_SYNC_ENABLED", False):
        return _disabled_sync_result()

    media_root = Path(settings.MEDIA_ROOT)
    referenced_names = set()
    missing_actions = []

    for model, field in _iter_file_fields():
        queryset = model.objects.exclude(**{field.name: ""}).only("pk", field.name)
        for instance in queryset:
            field_file = getattr(instance, field.name)
            relative_name = (field_file.name or "").replace("\\", "/").strip("/")
            if not relative_name:
                continue

            referenced_names.add(relative_name)
            if not (media_root / relative_name).is_file():
                action = _handle_missing_file(instance, field)
                if action:
                    missing_actions.append(action)

    blocked_files = []
    if media_root.exists():
        for file_path in media_root.rglob("*"):
            if not file_path.is_file():
                continue
            if ".trash" in file_path.parts:
                continue
            relative_name = file_path.relative_to(media_root).as_posix()
            if _is_protected_media(relative_name):
                continue
            if relative_name not in referenced_names:
                blocked_files.append({"from": relative_name, "reason": "script_delete_blocked"})

        for directory in sorted(
            (
                path
                for path in media_root.rglob("*")
                if path.is_dir() and ".trash" not in path.parts
            ),
            key=lambda path: len(path.parts),
            reverse=True,
        ):
            try:
                if directory.relative_to(media_root).as_posix().startswith("audio/"):
                    continue
                directory.rmdir()
            except OSError:
                pass

    return {
        "missing_actions": missing_actions,
        "trashed_files": [],
        "blocked_files": blocked_files,
    }


def maybe_sync_site_media():
    global _LAST_SYNC_AT

    if not getattr(settings, "MEDIA_SYNC_ENABLED", False):
        return None

    interval = max(0, int(getattr(settings, "MEDIA_SYNC_INTERVAL_SECONDS", 10)))
    now = time.monotonic()
    if interval and now - _LAST_SYNC_AT < interval:
        return None

    with _SYNC_LOCK:
        now = time.monotonic()
        if interval and now - _LAST_SYNC_AT < interval:
            return None
        result = sync_site_media()
        _LAST_SYNC_AT = now
        return result
