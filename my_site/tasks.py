from celery import shared_task

from .media_sync import sync_site_media


@shared_task
def sync_site_media_task():
    return sync_site_media()
