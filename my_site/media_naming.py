from pathlib import PurePosixPath

from django.utils.text import get_valid_filename


def media_display_name(field_file) -> str:
    if not field_file:
        return ""
    return PurePosixPath(str(getattr(field_file, "name", ""))).name


def _sanitize_filename(filename: str) -> str:
    safe_name = get_valid_filename(PurePosixPath(filename or "").name)
    return safe_name or "file"


def dated_media_upload_to(prefix: str):
    prefix = prefix.strip("/")

    def upload_to(instance, filename):
        created = getattr(instance, "created", None)
        if created:
            return f"{prefix}/{created:%Y/%m/%d}/{_sanitize_filename(filename)}"
        return f"{prefix}/%Y/%m/%d/{_sanitize_filename(filename)}"

    return upload_to


def static_media_upload_to(prefix: str):
    prefix = prefix.strip("/")

    def upload_to(instance, filename):
        return f"{prefix}/{_sanitize_filename(filename)}"

    return upload_to
