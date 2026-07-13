from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from blog.models import AudioPost, Post, VideoPost
from images.models import Album, AlbumImage, ImagePost

from .media_helpers import invalidate_cache_keys
from .media_sync import sync_deleted_instance_media


def _clear_related_caches(instance):
    if isinstance(instance, AudioPost):
        invalidate_cache_keys("audio_list:ids", "audio_list:items")
    elif isinstance(instance, ImagePost):
        invalidate_cache_keys("gallery_list:valid_image_ids")
    elif isinstance(instance, (Album, AlbumImage)):
        invalidate_cache_keys("album_list:valid_album_ids")


@receiver(post_delete)
def move_media_files_after_delete(sender, instance, **kwargs):
    if not hasattr(instance, "_meta"):
        return
    sync_deleted_instance_media(instance)


@receiver(post_save)
def clear_related_caches_after_save(sender, instance, **kwargs):
    if isinstance(instance, (AudioPost, VideoPost, ImagePost, Album, AlbumImage)):
        _clear_related_caches(instance)
