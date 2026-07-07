from pathlib import Path
import threading
import time

from django.apps import apps
from django.conf import settings
from django.db.models import FileField

from .media_cleanup import move_media_file_to_trash

_SYNC_LOCK = threading.Lock()
_LAST_SYNC_AT = 0.0


def _iter_file_fields():
    for model in apps.get_models():
        for field in model._meta.get_fields():
            if isinstance(field, FileField):
                yield model, field


def _handle_missing_file(instance, field):
    field_file = getattr(instance, field.name)
    relative_name = (field_file.name or "").replace("\\", "/").strip("/")
    if not relative_name:
        return None

    if field.null:
        setattr(instance, field.name, None)
    else:
        setattr(instance, field.name, "")

    if field.blank or field.null:
        instance.save(update_fields=[field.name])
        return {"type": "cleared_field", "model": instance._meta.label, "id": instance.pk, "field": field.name}

    instance.delete()
    return {"type": "deleted_record", "model": instance._meta.label, "id": instance.pk, "field": field.name}


def sync_site_media():
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

    trashed_files = []
    if media_root.exists():
        for file_path in media_root.rglob("*"):
            if not file_path.is_file():
                continue
            if ".trash" in file_path.parts:
                continue
            relative_name = file_path.relative_to(media_root).as_posix()
            if relative_name not in referenced_names:
                trash_name = move_media_file_to_trash(relative_name)
                if trash_name:
                    trashed_files.append({"from": relative_name, "to": trash_name})

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
                directory.rmdir()
            except OSError:
                pass

    return {
        "missing_actions": missing_actions,
        "trashed_files": trashed_files,
    }


def maybe_sync_site_media():
    global _LAST_SYNC_AT

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
