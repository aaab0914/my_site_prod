from django.core.exceptions import ValidationError


MB = 1024 * 1024

IMAGE_MAX_SIZE = 5 * MB
AUDIO_MAX_SIZE = 10 * MB
VIDEO_MAX_SIZE = 50 * MB

IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp")

AUDIO_CONTENT_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/ogg",
}
AUDIO_EXTENSIONS = (".mp3", ".wav", ".ogg")

VIDEO_CONTENT_TYPES = {
    "video/mp4",
    "video/webm",
    "video/quicktime",
    "video/x-matroska",
}
VIDEO_EXTENSIONS = (".mp4", ".webm", ".mov", ".mkv")


def validate_upload_size(upload, max_size, label):
    if upload.size > max_size:
        max_mb = max_size // MB
        raise ValidationError(f"{label} upload must be {max_mb}MB or smaller.")
    return upload


def validate_upload_type(upload, *, allowed_types, allowed_extensions, label, type_message, extension_message):
    if getattr(upload, "content_type", "") not in allowed_types:
        raise ValidationError(type_message)
    if not upload.name.lower().endswith(allowed_extensions):
        raise ValidationError(extension_message)
    return upload


def validate_image_upload(upload, *, label="Image"):
    validate_upload_type(
        upload,
        allowed_types=IMAGE_CONTENT_TYPES,
        allowed_extensions=IMAGE_EXTENSIONS,
        label=label,
        type_message=f"{label} must be a JPEG, PNG, or WebP file.",
        extension_message=f"{label} extension must be .jpg, .jpeg, .png, or .webp.",
    )
    return validate_upload_size(upload, IMAGE_MAX_SIZE, label)


def validate_audio_upload(upload):
    validate_upload_type(
        upload,
        allowed_types=AUDIO_CONTENT_TYPES,
        allowed_extensions=AUDIO_EXTENSIONS,
        label="Audio",
        type_message="Audio upload must be an MP3, WAV, or OGG file.",
        extension_message="Audio file extension must be .mp3, .wav, or .ogg.",
    )
    return validate_upload_size(upload, AUDIO_MAX_SIZE, "Audio")


def validate_video_upload(upload):
    validate_upload_type(
        upload,
        allowed_types=VIDEO_CONTENT_TYPES,
        allowed_extensions=VIDEO_EXTENSIONS,
        label="Video",
        type_message="Video upload must be an MP4, WebM, MOV, or MKV file.",
        extension_message="Video file extension must be .mp4, .webm, .mov, or .mkv.",
    )
    return validate_upload_size(upload, VIDEO_MAX_SIZE, "Video")
