from pathlib import Path

from django.conf import settings

from blog.models import Post
from .models import ImagePost


def sync_gallery_media():
    if not getattr(settings, "MEDIA_SYNC_ENABLED", True):
        return {
            "missing_records": 0,
            "created_records": 0,
            "missing_record_ids": [],
        }

    media_root = Path(settings.MEDIA_ROOT)
    missing_ids = []
    created_records = 0

    for image in ImagePost.objects.exclude(image="").only("id", "image"):
        image_name = (image.image.name or "").replace("\\", "/").strip("/")
        if not image_name:
            missing_ids.append(image.id)
            continue
        if not (media_root / image_name).is_file():
            missing_ids.append(image.id)

    for post in Post.objects.exclude(cover_image="").exclude(cover_image__isnull=True).select_related("author"):
        image_name = (post.cover_image.name or "").replace("\\", "/").strip("/")
        if not image_name:
            continue
        if not (media_root / image_name).is_file():
            continue

        _, created = ImagePost.objects.get_or_create(
            image=image_name,
            defaults={
                "title": post.title[:200],
                "description": "",
                "uploaded_by": post.author,
            },
        )
        if created:
            created_records += 1

    return {
        "missing_records": len(missing_ids),
        "created_records": created_records,
        "missing_record_ids": missing_ids,
    }
