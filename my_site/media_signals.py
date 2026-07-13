from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver

from .media_cleanup import cleanup_instance_media_files, prepare_instance_media_cleanup


@receiver(pre_delete)
def collect_media_files_before_delete(sender, instance, **kwargs):
    prepare_instance_media_cleanup(instance)


@receiver(post_delete)
def move_media_files_after_delete(sender, instance, **kwargs):
    cleanup_instance_media_files(instance)
