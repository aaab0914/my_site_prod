from datetime import datetime
from pathlib import Path
import shutil

from django.conf import settings


def move_media_file_to_trash(relative_name):
    media_root = Path(settings.MEDIA_ROOT)
    source_path = media_root / relative_name
    if not source_path.exists() or not source_path.is_file():
        return None

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    normalized_relative_name = Path(relative_name.replace("\\", "/"))
    trash_root = Path(settings.BASE_DIR) / ".trash" / timestamp
    target_path = trash_root / normalized_relative_name
    target_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.move(str(source_path), str(target_path))
    except FileNotFoundError:
        return None
    return target_path.relative_to(Path(settings.BASE_DIR)).as_posix()
