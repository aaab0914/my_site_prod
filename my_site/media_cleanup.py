from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import shutil

from django.conf import settings
from django.db.models import FileField

from .request_context import is_browser_delete_request
from .runtime_file_guards import ensure_runtime_file_not_protected


def _normalize_relative_name(relative_name):
    return (relative_name or "").replace("\\", "/").strip("/")


def _file_fields(instance):
    for field in instance._meta.get_fields():
        if isinstance(field, FileField):
            yield field


def collect_instance_media_files(instance):
    if not hasattr(instance, "_meta"):
        return []

    files_to_trash = []
    for field in _file_fields(instance):
        field_file = getattr(instance, field.name, None)
        relative_name = _normalize_relative_name(getattr(field_file, "name", ""))
        if relative_name:
            files_to_trash.append(relative_name)
    return files_to_trash


def prepare_instance_media_cleanup(instance):
    instance._media_files_to_trash = collect_instance_media_files(instance)


@contextmanager
def authorized_media_delete():
    yield


def move_media_file_to_trash(relative_name):
    if not is_browser_delete_request():
        return None

    normalized_relative_name = _normalize_relative_name(relative_name)
    if not normalized_relative_name:
        return None

    media_root = Path(settings.MEDIA_ROOT)
    source_path = media_root / normalized_relative_name
    ensure_runtime_file_not_protected(source_path, action="trash move")
    if not source_path.exists() or not source_path.is_file():
        return None

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    trash_root = Path(settings.BASE_DIR) / ".trash" / timestamp
    target_path = trash_root / Path(normalized_relative_name)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.move(str(source_path), str(target_path))
    except FileNotFoundError:
        return None
    return target_path.relative_to(Path(settings.BASE_DIR)).as_posix()


def cleanup_instance_media_files(instance):
    if not is_browser_delete_request():
        return []

    trashed_files = []
    for relative_name in getattr(instance, "_media_files_to_trash", []):
        trashed_path = move_media_file_to_trash(relative_name)
        if trashed_path is not None:
            trashed_files.append(trashed_path)
    return trashed_files
