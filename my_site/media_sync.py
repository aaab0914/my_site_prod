from django.db.models import FileField

from .media_cleanup import authorized_media_delete, move_media_file_to_trash
from .media_helpers import invalidate_cache_keys

def _clear_related_caches(instance):
    label = instance._meta.label
    if label == "blog.AudioPost":
        invalidate_cache_keys("audio_list:ids", "audio_list:items")
    elif label == "blog.VideoPost":
        invalidate_cache_keys("video_list:ids", "video_list:items")
    elif label == "images.ImagePost":
        invalidate_cache_keys("gallery_list:valid_image_ids")
    elif label in {"images.Album", "images.AlbumImage"}:
        invalidate_cache_keys("album_list:valid_album_ids")


def sync_deleted_instance_media(instance):
    moved_files = []
    with authorized_media_delete():
        for field in instance._meta.get_fields():
            if not isinstance(field, FileField):
                continue
            field_file = getattr(instance, field.name, None)
            relative_name = getattr(field_file, "name", "") or ""
            relative_name = relative_name.replace("\\", "/").strip("/")
            if not relative_name:
                continue
            trashed_to = move_media_file_to_trash(relative_name)
            if trashed_to:
                moved_files.append({"from": relative_name, "to": trashed_to})
    _clear_related_caches(instance)
    return moved_files


def sync_gallery_media():
    return {
        "missing_records": 0,
        "created_records": 0,
        "missing_record_ids": [],
        "deleted_records": 0,
        "cleared_fields": 0,
        "trashed_files": [],
        "missing_actions": [],
        "orphaned_files": [],
    }


def sync_site_media():
    return {
        "enabled": False,
        "reason": "Automatic media sync is disabled. Media files move to .trash only when users delete objects in the site UI.",
        "missing_actions": [],
        "orphaned_files": [],
        "trashed_files": [],
        "deleted_records": 0,
        "cleared_fields": 0,
        "gallery_sync": sync_gallery_media(),
    }


def maybe_sync_site_media():
    return None
