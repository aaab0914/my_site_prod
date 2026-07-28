from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django import forms
from django.db.models import Count, Q
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html, format_html_join
from django.utils.timezone import now
import taggit.admin
from taggit.models import Tag

from .models import AudioPost, AuditLog, Comment, Post, VideoPost
from my_site.tagging import normalize_post_tags, normalize_tag_name, normalize_tag_slug


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


def _template_inventory():
    base_dir = Path(settings.BASE_DIR)
    roots = [
        base_dir / "blog" / "templates",
        base_dir / "images" / "templates",
        base_dir / "my_site" / "templates",
    ]
    frontend_map = {
        "blog/templates/blog/audio/audio_list.html": "/blog/audio/list/",
        "blog/templates/blog/audio/audio_post_delete.html": "/blog/audio/list/",
        "blog/templates/blog/audio/audio_post_delete_success.html": "/blog/audio/delete/success/",
        "blog/templates/blog/audio/audio_post_edit.html": "/blog/audio/list/",
        "blog/templates/blog/audio/upload_audio.html": "/blog/audio/upload/",
        "blog/templates/blog/base.html": "/blog/",
        "blog/templates/blog/comment/add_comment.html": "/blog/",
        "blog/templates/blog/comment/add_comment_success.html": "/blog/",
        "blog/templates/blog/comment/add_picture_to_comment.html": "/blog/",
        "blog/templates/blog/comment/delete_comment.html": "/blog/",
        "blog/templates/blog/comment/delete_comment_success.html": "/blog/",
        "blog/templates/blog/comment/edit_comment.html": "/blog/",
        "blog/templates/blog/hero_base.html": "/blog/",
        "blog/templates/blog/pagination.html": "/blog/",
        "blog/templates/blog/post/all_posts_list.html": "/blog/",
        "blog/templates/blog/post/create_post.html": "/blog/create/",
        "blog/templates/blog/post/create_post_success.html": "/blog/create/",
        "blog/templates/blog/post/latest_posts.html": "/blog/",
        "blog/templates/blog/post/post_delete.html": "/blog/",
        "blog/templates/blog/post/post_delete_success.html": "/blog/post_delete_success/",
        "blog/templates/blog/post/post_detail.html": "/blog/",
        "blog/templates/blog/post/post_edit.html": "/blog/",
        "blog/templates/blog/post/search_post.html": "/blog/search/",
        "blog/templates/blog/video/upload_video.html": "/blog/video/upload/",
        "blog/templates/blog/video/video_delete.html": "/blog/video/list/",
        "blog/templates/blog/video/video_detail.html": "/blog/video/list/",
        "blog/templates/blog/video/video_edit.html": "/blog/video/list/",
        "blog/templates/blog/video/video_list.html": "/blog/video/list/",
        "images/templates/images/album_delete_confirm.html": "/blog/album/",
        "images/templates/images/album_detail.html": "/blog/album/",
        "images/templates/images/album_edit.html": "/blog/album/",
        "images/templates/images/album_list.html": "/blog/album/",
        "images/templates/images/album_upload.html": "/blog/album/upload/",
        "images/templates/images/gallery_delete_confirm.html": "/blog/gallery/",
        "images/templates/images/gallery_detail.html": "/blog/gallery/",
        "images/templates/images/gallery_edit.html": "/blog/gallery/",
        "images/templates/images/gallery_list.html": "/blog/gallery/",
        "images/templates/images/gallery_upload.html": "/blog/gallery/upload/",
        "my_site/templates/index.html": "/",
        "blog/templates/admin/base_site.html": "/secure-console-7f9a2c-admin/",
        "blog/templates/admin/blog/post/change_form.html": "/secure-console-7f9a2c-admin/blog/post/",
        "blog/templates/admin/custom_index.html": "/secure-console-7f9a2c-admin/",
        "blog/templates/admin/index.html": "/secure-console-7f9a2c-admin/",
        "blog/templates/admin/sites/site/change_list.html": "/secure-console-7f9a2c-admin/sites/site/",
        "blog/templates/admin/system_status.html": "/secure-console-7f9a2c-admin/system-status/",
    }
    items = []
    index = 1
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.html")):
            rel = path.relative_to(base_dir)
            items.append(
                {
                    "id": index,
                    "name": path.name,
                    "relative_path": rel.as_posix(),
                    "frontend_path": frontend_map.get(rel.as_posix(), ""),
                }
            )
            index += 1
    return items


def _resolve_log_path(logs_dir: Path, family: str, date_string: str) -> Path:
    structured = logs_dir / family / date_string[:7] / f"{family}-{date_string}.log"
    if structured.exists():
        return structured
    legacy = logs_dir / date_string[:7] / f"{family}-{date_string}.log"
    return structured if structured.exists() else legacy


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
    backup_files = sorted(backups_dir.glob("*.sql"), key=lambda p: p.stat().st_mtime, reverse=True) if backups_dir.exists() else []
    valid_backup_files = [item for item in backup_files if item.exists() and item.stat().st_size > 0]
    latest_backup = valid_backup_files[0] if valid_backup_files else (backup_files[0] if backup_files else None)
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
            "is_valid": item.stat().st_size > 0,
        }
        for item in backup_files[:10]
    ]
    recent_audit_count = AuditLog.objects.filter(timestamp__gte=today.replace(minute=0, second=0, microsecond=0)).count()
    context = {
        **admin.site.each_context(request),
        "title": "System Status",
        "subtitle": "Daily logs, backup status, and audit controls",
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
        "audit_rate_limit_summary": "Repeated safe requests are deduplicated to at most one audit row per hour per IP/path/method/status.",
        "recent_audit_count": recent_audit_count,
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

try:
    admin.site.unregister(Tag)
except admin.sites.NotRegistered:
    pass

try:
    admin.site.unregister(Site)
except admin.sites.NotRegistered:
    pass


class PostAdminForm(forms.ModelForm):
    body = forms.CharField(
        widget=forms.Textarea(
            attrs={"rows": 16, "cols": 140, "style": "width: 100%; min-height: 24em; resize: vertical;"}
        )
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
