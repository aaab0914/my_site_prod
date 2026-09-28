from contextlib import suppress
from datetime import datetime
from pathlib import Path

from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.sites.models import Site
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.html import format_html
from django.utils.timezone import now
from taggit.models import Tag

from my_site.tagging import normalize_post_tags

from .models import AudioPost, AuditLog, Post, VideoPost


def make_active(modeladmin, request, queryset):
    queryset.update(active=True)


def make_inactive(modeladmin, request, queryset):
    queryset.update(active=False)


def _tail_lines(path: Path, limit: int = 20):
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            lines = handle.readlines()
        return [line.rstrip("\n") for line in lines[-limit:]]
    except OSError:
        return []


def _human_size(size: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size} B"


def _resolve_log_path(logs_dir: Path, family: str, date_string: str) -> Path:
    structured = logs_dir / family / date_string[:7] / f"{family}-{date_string}.log"
    if structured.exists():
        return structured
    return logs_dir / date_string[:7] / f"{family}-{date_string}.log"


def admin_system_status_view(request):
    base_dir = Path(settings.BASE_DIR)
    logs_dir = base_dir / "logs"
    backups_dir = base_dir / "backups" / "db"
    today = now()
    date_string = today.strftime("%Y-%m-%d")

    log_prefixes = [
        ("django", "Django"),
        ("django-error", "Django Error"),
        ("gunicorn-access", "Gunicorn Access"),
        ("gunicorn-error", "Gunicorn Error"),
        ("celery", "Celery"),
        ("nginx-access", "Nginx Access"),
        ("nginx-error", "Nginx Error"),
    ]

    log_statuses = []
    for family, label in log_prefixes:
        path = _resolve_log_path(logs_dir, family, date_string)
        exists = path.exists()
        stat = path.stat() if exists else None
        log_statuses.append(
            {
                "label": label,
                "family": family,
                "path": path,
                "exists": exists,
                "size": _human_size(stat.st_size) if stat else "-",
                "modified": datetime.fromtimestamp(stat.st_mtime) if stat else None,
                "tail": _tail_lines(path, limit=8),
            }
        )

    backup_files = (
        sorted(backups_dir.glob("*.sql"), key=lambda p: p.stat().st_mtime, reverse=True)
        if backups_dir.exists()
        else []
    )
    valid_backup_files = [
        item for item in backup_files if item.exists() and item.stat().st_size > 0
    ]
    latest_backup = (
        valid_backup_files[0]
        if valid_backup_files
        else (backup_files[0] if backup_files else None)
    )

    backup_log_path = logs_dir / "backup.log"
    backup_log_tail = _tail_lines(backup_log_path, limit=20)
    latest_backup_success = bool(
        latest_backup and latest_backup.exists() and latest_backup.stat().st_size > 0
    )
    latest_backup_message = "No backup record found."

    effective_events = []
    for line in backup_log_tail:
        if (
            "Backup succeeded" in line
            or "备份成功" in line
            or "Skip backup" in line
            or "备份失败" in line
            or "Backup failed" in line
        ):
            effective_events.append(line)

    if effective_events:
        latest_backup_message = effective_events[-1]
        latest_backup_success = (
            "Backup succeeded" in latest_backup_message
            or "备份成功" in latest_backup_message
            or "Skip backup" in latest_backup_message
        )
    elif latest_backup_success and latest_backup:
        latest_backup_message = f"Latest backup file looks valid: {latest_backup.name}"

    backup_file_rows = [
        {
            "name": item.name,
            "modified": datetime.fromtimestamp(item.stat().st_mtime),
            "size": _human_size(item.stat().st_size),
            "is_valid": item.stat().st_size > 0,
        }
        for item in backup_files[:10]
    ]

    recent_audit_count = AuditLog.objects.filter(
        timestamp__gte=today.replace(minute=0, second=0, microsecond=0)
    ).count()

    context = {
        **admin.site.each_context(request),
        "title": "System Status",
        "subtitle": "Daily logs, backup status, and audit controls",
        "log_statuses": log_statuses,
        "backup_log_tail": backup_log_tail,
        "backup_log_path": backup_log_path,
        "latest_backup": latest_backup,
        "latest_backup_size": _human_size(latest_backup.stat().st_size)
        if latest_backup
        else "-",
        "latest_backup_mtime": datetime.fromtimestamp(latest_backup.stat().st_mtime)
        if latest_backup
        else None,
        "latest_backup_success": latest_backup_success,
        "latest_backup_message": latest_backup_message,
        "backup_count": len(backup_files),
        "backup_files": backup_file_rows,
        "audit_rate_limit_summary": (
            "Repeated safe requests are deduplicated to at most one audit row "
            "per hour per IP/path/method/status."
        ),
        "recent_audit_count": recent_audit_count,
    }
    return TemplateResponse(request, "admin/system_status.html", context)


_original_get_urls = admin.site.get_urls


def _custom_admin_get_urls():
    custom_urls = [
        path(
            "system-status/",
            admin.site.admin_view(admin_system_status_view),
            name="system_status",
        ),
    ]
    return custom_urls + _original_get_urls()


admin.site.get_urls = _custom_admin_get_urls
admin.site.index_template = "admin/custom_index.html"

with suppress(admin.sites.NotRegistered):
    admin.site.unregister(Tag)

with suppress(admin.sites.NotRegistered):
    admin.site.unregister(Site)


class PostAdminForm(forms.ModelForm):
    body = forms.CharField(
        max_length=5000,
        widget=forms.Textarea(
            attrs={
                "rows": 16,
                "cols": 140,
                "style": "width: 100%; min-height: 24em; resize: vertical;",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["body"].help_text = ""

    class Meta:
        model = Post
        fields = ["title", "slug", "author", "body", "publish", "status", "tags"]
        widgets = {
            "title": forms.TextInput(attrs={"style": "width: 100%; max-width: 980px;"}),
            "slug": forms.TextInput(attrs={"style": "width: 100%; max-width: 980px;"}),
        }

    class Media:
        css = {"all": ("admin/css/post_admin.css", "admin/css/site_admin.css")}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm
    change_form_template = "admin/blog/post/change_form.html"
    list_display = ["title", "slug", "author", "publish", "status"]
    list_filter = ["status", "created", "publish", "author"]
    search_fields = ["title", "body"]
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ["author"]
    date_hierarchy = "publish"
    ordering = ["status", "publish"]
    show_facets = admin.ShowFacets.ALWAYS

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        normalize_post_tags(form.instance)


@admin.register(AudioPost)
class AudioPostAdmin(admin.ModelAdmin):
    list_display = ["music_name", "uploaded_by", "created", "updated", "active"]
    list_filter = ["active", "created", "updated", "uploaded_by"]
    search_fields = ["music_name", "description", "uploaded_by__username"]
    readonly_fields = ["audio_preview", "cover_preview", "created", "updated"]
    raw_id_fields = ["uploaded_by"]
    ordering = ["-created"]
    actions = [make_active, make_inactive]

    @admin.display(description="Audio Preview")
    def audio_preview(self, obj):
        if not obj.audio_file:
            return "-"
        return format_html(
            '<audio controls preload="none" style="width:220px;">'
            '<source src="{}"></audio>',
            obj.get_audio_proxy_url(),
        )

    @admin.display(description="Cover Preview")
    def cover_preview(self, obj):
        if not obj.cover_image:
            return "-"
        return format_html(
            '<img src="{}" alt="cover" '
            'style="width:56px;height:56px;object-fit:cover;border-radius:6px;">',
            obj.get_cover_image_proxy_url(),
        )


@admin.register(VideoPost)
class VideoPostAdmin(admin.ModelAdmin):
    list_display = ["title", "uploaded_by", "created", "updated"]
    list_filter = ["created", "updated", "uploaded_by"]
    search_fields = ["title", "description", "uploaded_by__username"]
    readonly_fields = ["video_preview", "created", "updated"]
    raw_id_fields = ["uploaded_by"]
    ordering = ["-created"]

    @admin.display(description="Preview")
    def video_preview(self, obj):
        if not obj.video_file:
            return "-"
        return format_html(
            '<video controls preload="none" style="width:180px;max-height:110px;">'
            '<source src="{}"></video>',
            obj.get_video_proxy_url(),
        )
