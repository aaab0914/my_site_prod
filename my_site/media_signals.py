from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver

from .media_cleanup import handle_instance_post_delete, handle_instance_pre_delete


@receiver(pre_delete)
def collect_media_files_before_delete(sender, instance, **kwargs):
    handle_instance_pre_delete(instance)


@receiver(post_delete)
def move_media_files_after_delete(sender, instance, **kwargs):
    handle_instance_post_delete(instance)
