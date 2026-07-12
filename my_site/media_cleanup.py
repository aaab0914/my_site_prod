from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
import shutil

from django.conf import settings

_MEDIA_DELETE_AUTHORIZED = ContextVar("media_delete_authorized", default=False)


def is_media_delete_authorized():
    return bool(_MEDIA_DELETE_AUTHORIZED.get())


@contextmanager
def authorized_media_delete():
    token = _MEDIA_DELETE_AUTHORIZED.set(True)
    try:
        yield
    finally:
        _MEDIA_DELETE_AUTHORIZED.reset(token)


def move_media_file_to_trash(relative_name):
    if not is_media_delete_authorized():
        return None

    media_root = Path(settings.MEDIA_ROOT)
    source_path = media_root / relative_name
    if not source_path.exists() or not source_path.is_file():
        return None

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    normalized_relative_name = Path(relative_name.replace("\\", "/"))
    project_root = Path(settings.BASE_DIR)
    trash_root = project_root.parent / ".trash" / project_root.name / timestamp
    target_path = trash_root / normalized_relative_name
    target_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.move(str(source_path), str(target_path))
    except FileNotFoundError:
        return None
    return target_path.relative_to(project_root.parent).as_posix()
