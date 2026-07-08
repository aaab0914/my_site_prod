from pathlib import Path

from django.conf import settings

from my_site.media_cleanup import move_media_file_to_trash
from .models import ImagePost


def sync_gallery_media():
    media_root = Path(settings.MEDIA_ROOT)
    posts_root = media_root / "posts"
    referenced_names = set()
    missing_ids = []

    for image in ImagePost.objects.exclude(image="").only("id", "image"):
        image_name = (image.image.name or "").replace("\\", "/").strip("/")
        if not image_name:
            missing_ids.append(image.id)
            continue
        referenced_names.add(image_name)
        if not (media_root / image_name).is_file():
            missing_ids.append(image.id)

    if missing_ids:
        ImagePost.objects.filter(id__in=missing_ids).delete()

    trashed_files = []
    if posts_root.exists():
        for file_path in posts_root.rglob("*"):
            if not file_path.is_file():
                continue
            relative_name = file_path.relative_to(media_root).as_posix()
            if relative_name not in referenced_names:
                trash_name = move_media_file_to_trash(relative_name)
                if trash_name:
                    trashed_files.append(
                        {
                            "from": relative_name,
                            "to": trash_name,
                        }
                    )

        for directory in sorted(
            (path for path in posts_root.rglob("*") if path.is_dir()),
            key=lambda path: len(path.parts),
            reverse=True,
        ):
            try:
                directory.rmdir()
            except OSError:
                pass

    return {
        "deleted_records": len(missing_ids),
        "trashed_files": trashed_files,
    }
