from pathlib import PurePosixPath

from django.utils.deconstruct import deconstructible
from django.utils.text import get_valid_filename


def media_display_name(field_file) -> str:
    if not field_file:
        return ""
    return PurePosixPath(str(getattr(field_file, "name", ""))).name


def _sanitize_filename(filename: str) -> str:
    safe_name = get_valid_filename(PurePosixPath(filename or "").name)
    return safe_name or "file"


@deconstructible
class DatedMediaUploadTo:
    def __init__(self, prefix: str):
        self.prefix = prefix.strip("/")

    def __call__(self, instance, filename):
        created = getattr(instance, "created", None)
        if created:
            return f"{self.prefix}/{created:%Y/%m/%d}/{_sanitize_filename(filename)}"
        return f"{self.prefix}/%Y/%m/%d/{_sanitize_filename(filename)}"

def dated_media_upload_to(prefix: str):
    return DatedMediaUploadTo(prefix)


@deconstructible
class StaticMediaUploadTo:
    def __init__(self, prefix: str):
        self.prefix = prefix.strip("/")

    def __call__(self, instance, filename):
        return f"{self.prefix}/{_sanitize_filename(filename)}"

def static_media_upload_to(prefix: str):
    return StaticMediaUploadTo(prefix)
