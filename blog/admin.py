"""
Django admin configuration for the blog application.
This module registers all models with the Django admin site and customizes
their list displays, filters, search fields, and actions.
"""

from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.contrib import admin, messages
from django import forms
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.timezone import now

from .models import Post, Comment, AudioPost, VideoPost, AuditLog


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
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} {unit}"
        value /= 1024
    return f"{size} B"


def admin_system_status_view(request):
    base_dir = Path(settings.BASE_DIR)
    logs_dir = base_dir / "logs"
    backups_dir = base_dir / "backups" / "db"
    today = now()
    month_dir = logs_dir / today.strftime("%Y-%m")

    log_prefixes = [
        ("django", "Django"),
        ("error", "Error"),
        ("gunicorn-access", "Gunicorn Access"),
        ("gunicorn-error", "Gunicorn Error"),
    ]

    log_statuses = []
    for prefix, label in log_prefixes:
        path = month_dir / f"{prefix}-{today.strftime('%Y-%m-%d')}.log"
        exists = path.exists()
        log_statuses.append(
            {
                "label": label,
                "path": path,
                "exists": exists,
                "size": _human_size(path.stat().st_size) if exists else "-",
                "modified": datetime.fromtimestamp(path.stat().st_mtime) if exists else None,
                "tail": _tail_lines(path, limit=8),
            }
        )

    backup_files = sorted(backups_dir.glob("*.sql"), key=lambda p: p.stat().st_mtime, reverse=True) if backups_dir.exists() else []
    latest_backup = backup_files[0] if backup_files else None
    backup_log_path = logs_dir / "backup.log"
    backup_log_tail = _tail_lines(backup_log_path, limit=20)

    latest_backup_success = bool(latest_backup and latest_backup.exists() and latest_backup.stat().st_size > 0)
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
        }
        for item in backup_files[:10]
    ]

    context = {
        **admin.site.each_context(request),
        "title": "System Status",
        "subtitle": "Daily logs and database backup status",
        "log_statuses": log_statuses,
        "backup_log_tail": backup_log_tail,
        "backup_log_path": backup_log_path,
        "latest_backup": latest_backup,
        "latest_backup_size": _human_size(latest_backup.stat().st_size) if latest_backup else "-",
        "latest_backup_mtime": datetime.fromtimestamp(latest_backup.stat().st_mtime) if latest_backup else None,
        "latest_backup_success": latest_backup_success,
        "latest_backup_message": latest_backup_message,
        "backup_count": len(backup_files),
        "backup_files": backup_file_rows,
    }
    return TemplateResponse(request, "admin/system_status.html", context)


_original_get_urls = admin.site.get_urls


def _custom_admin_get_urls():
    custom_urls = [
        path("system-status/", admin.site.admin_view(admin_system_status_view), name="system_status"),
    ]
    return custom_urls + _original_get_urls()


admin.site.get_urls = _custom_admin_get_urls
admin.site.index_template = "admin/custom_index.html"


class PostAdminForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = "__all__"
        widgets = {
            "title": forms.TextInput(attrs={"style": "width: 100%; max-width: 1180px;"}),
            "slug": forms.TextInput(attrs={"style": "width: 100%; max-width: 1180px;"}),
            "body": forms.Textarea(attrs={"rows": 20, "cols": 140, "style": "width: 100%; max-width: 1180px; min-height: 28em;"}),
        }

    class Media:
        css = {"all": ("admin/css/post_admin.css", "admin/css/site_admin.css")}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm
    list_display = ["title", "slug", "author", "publish", "status"]
    list_filter = ["status", "created", "publish", "author"]
    search_fields = ["title", "body"]
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ["author"]
    date_hierarchy = "publish"
    ordering = ["status", "publish"]
    show_facets = admin.ShowFacets.ALWAYS


class CommentAdminForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["post", "author", "email", "body", "active"]
        labels = {"body": "Comment"}
        widgets = {
            "body": forms.Textarea(attrs={"rows": 3, "cols": 120}),
        }

    class Media:
        css = {"all": ("admin/css/comment_admin.css",)}


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    form = CommentAdminForm
    list_display = ["comment_preview", "post", "author", "email", "created", "active"]
    list_filter = ["active", "created", "updated"]
    search_fields = ["author__username", "email", "body"]
    autocomplete_fields = ["post", "author"]

    @admin.display(description="Comment")
    def comment_preview(self, obj):
        text = (obj.body or "").strip().replace("\n", " ")
        return f"{text[:30].rstrip()}..." if len(text) > 30 else text


@admin.register(AudioPost)
class AudioPostAdmin(admin.ModelAdmin):
    list_display = [
        "music_name",
        "cover_preview",
        "audio_preview",
        "uploaded_by",
        "created",
        "updated",
        "active",
    ]
    list_filter = ["active", "created", "updated", "uploaded_by"]
    search_fields = ["music_name", "description", "uploaded_by__username"]
    readonly_fields = ["cover_preview", "audio_preview", "created", "updated"]
    raw_id_fields = ["uploaded_by"]
    autocomplete_fields = ["uploaded_by"]
    ordering = ["-created"]
    list_per_page = 20
    date_hierarchy = "created"
    actions = [make_active, make_inactive]
    show_facets = admin.ShowFacets.ALWAYS

    @admin.display(description="Cover")
    def cover_preview(self, obj):
        if not obj.cover_image:
            return "-"
        return format_html(
            '<img src="{}" alt="cover" style="width: 56px; height: 56px; object-fit: cover; border-radius: 6px;" />',
            obj.get_cover_image_proxy_url(),
        )

    @admin.display(description="Audio")
    def audio_preview(self, obj):
        if not obj.audio_file:
            return "-"
        return format_html(
            '<audio controls preload="none" style="width: 220px;"><source src="{}"></audio>',
            obj.get_audio_proxy_url(),
        )


@admin.register(VideoPost)
class VideoPostAdmin(admin.ModelAdmin):
    list_display = ["title", "video_preview", "uploaded_by", "created", "updated"]
    list_filter = ["created", "updated", "uploaded_by"]
    search_fields = ["title", "description", "uploaded_by__username"]
    readonly_fields = ["video_preview", "created", "updated"]
    raw_id_fields = ["uploaded_by"]
    autocomplete_fields = ["uploaded_by"]
    ordering = ["-created"]
    list_per_page = 20
    date_hierarchy = "created"
    show_facets = admin.ShowFacets.ALWAYS

    @admin.display(description="Preview")
    def video_preview(self, obj):
        if not obj.video_file:
            return "-"
        return format_html(
            '<video controls preload="metadata" style="width: 180px; max-height: 110px; border-radius: 6px;"><source src="{}"></video>',
            obj.get_video_proxy_url(),
        )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "method", "path", "status_code", "user", "ip_address", "response_time"]
    list_filter = ["method", "status_code", "timestamp"]
    search_fields = ["path", "ip_address", "user__username"]
    readonly_fields = ["user", "method", "path", "ip_address", "status_code", "response_time", "timestamp"]
    list_per_page = 50
    date_hierarchy = "timestamp"

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["system_status_url"] = reverse("admin:system_status")
        return super().changelist_view(request, extra_context=extra_context)
