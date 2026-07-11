from django.db.models import FileField
from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver

from blog.models import AudioPost, Post, VideoPost
from images.models import Album, AlbumImage, ImagePost

from .media_cleanup import move_media_file_to_trash
from .media_helpers import invalidate_cache_keys


def _file_fields(instance):
    for field in instance._meta.get_fields():
        if isinstance(field, FileField):
            yield field


def _clear_related_caches(instance):
    if isinstance(instance, AudioPost):
        invalidate_cache_keys("audio_list:ids", "audio_list:items")
    elif isinstance(instance, ImagePost):
        invalidate_cache_keys("gallery_list:valid_image_ids")
    elif isinstance(instance, (Album, AlbumImage)):
        invalidate_cache_keys("album_list:valid_album_ids")


@receiver(pre_delete)
def collect_media_files_before_delete(sender, instance, **kwargs):
    if not hasattr(instance, "_meta"):
        return

    files_to_trash = []
    for field in _file_fields(instance):
        field_file = getattr(instance, field.name, None)
        relative_name = getattr(field_file, "name", "") or ""
        relative_name = relative_name.replace("\\", "/").strip("/")
        if relative_name:
            files_to_trash.append(relative_name)

    instance._media_files_to_trash = files_to_trash


@receiver(post_delete)
def move_media_files_after_delete(sender, instance, **kwargs):
    for relative_name in getattr(instance, "_media_files_to_trash", []):
        move_media_file_to_trash(relative_name)
    _clear_related_caches(instance)


@receiver(post_save)
def clear_related_caches_after_save(sender, instance, **kwargs):
    if isinstance(instance, (AudioPost, VideoPost, ImagePost, Album, AlbumImage)):
        _clear_related_caches(instance)
