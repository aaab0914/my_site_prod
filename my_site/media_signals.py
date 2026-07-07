from django.db.models import FileField
from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver

from .media_cleanup import move_media_file_to_trash


def _file_fields(instance):
    for field in instance._meta.get_fields():
        if isinstance(field, FileField):
            yield field


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
