"""
Django admin configuration for the blog application.
This module registers all models with the Django admin site and customizes
their list displays, filters, search fields, and actions.
"""

from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django import forms
from django.db.models import Count, Q
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html, format_html_join
from django.utils.timezone import now
from django.utils.text import slugify
import taggit.admin
from taggit.models import Tag

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
            attrs={
                "rows": 16,
                "cols": 140,
                "style": "width: 100%; min-height: 24em; resize: vertical;",
            }
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


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["tag_name", "post_count", "published_post_count", "latest_post"]
    search_fields = ["name", "slug"]
    ordering = ["name"]
    list_per_page = 50
    show_facets = admin.ShowFacets.ALWAYS
    readonly_fields = ["linked_posts"]
    fields = ["name", "slug", "linked_posts"]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        post_content_type = ContentType.objects.get_for_model(Post)
        return queryset.annotate(
            post_count_value=Count(
                "taggit_taggeditem_items",
                filter=Q(taggit_taggeditem_items__content_type=post_content_type),
                distinct=True,
            )
        )

    @admin.display(description="Tag", ordering="name")
    def tag_name(self, obj):
        name = (obj.name or "").strip().lower()
        return name if name.startswith("#") else f"#{name}"

    @admin.display(description="Posts", ordering="post_count_value")
    def post_count(self, obj):
        return obj.post_count_value

    @admin.display(description="Published")
    def published_post_count(self, obj):
        post_content_type = ContentType.objects.get_for_model(Post)
        return Post.objects.filter(
            status=Post.Status.PUBLISHED,
            id__in=obj.taggit_taggeditem_items.filter(content_type=post_content_type).values_list("object_id", flat=True),
        ).count()

    @admin.display(description="Latest Post")
    def latest_post(self, obj):
        post = (
            Post.objects.filter(tags__id=obj.id)
            .select_related("author")
            .order_by("-publish")
            .first()
        )
        if not post:
            return "-"
        return format_html(
            '<a href="{}">{}</a> <span style="color:#6b7280;">| {} | {}</span>',
            post.get_absolute_url(),
            post.title,
            post.author.username,
            post.publish.strftime("%Y-%m-%d"),
        )

    @admin.display(description="Related Posts")
    def linked_posts(self, obj):
        posts = (
            Post.objects.filter(tags__id=obj.id)
            .select_related("author")
            .order_by("-publish")
        )
        if not posts.exists():
            return "No related posts."

        rows = []
        for post in posts:
            url = post.get_absolute_url()
            rows.append(
                (
                    url,
                    post.title,
                    post.author.username,
                    post.get_status_display(),
                    post.publish.strftime("%Y-%m-%d %H:%M"),
                )
            )

        return format_html(
            '<div style="max-width: 980px; padding: 12px 0;"><ul style="margin: 0; padding-left: 18px;">{}</ul></div>',
            format_html_join(
                "",
                '<li><a href="{}">{}</a> <span style="color:#6b7280;">| {} | {} | {}</span></li>',
                rows,
            ),
        )

    def save_model(self, request, obj, form, change):
        normalized = (obj.name or "").strip().lower()
        if normalized and not normalized.startswith("#"):
            normalized = f"#{normalized}"
        obj.name = normalized
        obj.slug = slugify(normalized.lstrip("#"))
        super().save_model(request, obj, form, change)


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ["id", "domain", "name", "quick_links"]
    search_fields = ["domain", "name"]
    readonly_fields = ["site_links"]
    fields = ["domain", "name", "site_links"]
    change_list_template = "admin/sites/site/change_list.html"
    actions = None

    @admin.display(description="Quick Links")
    def quick_links(self, obj):
        base_url = f"http://{obj.domain}".rstrip("/")
        links = [
            (f"{base_url}/", "Home"),
            (f"{base_url}/blog/", "Blog"),
            (f"{base_url}/blog/create/", "Create"),
            (f"{base_url}/blog/audio/list/", "Audio"),
            (f"{base_url}/blog/audio/upload/", "Upload Audio"),
            (f"{base_url}/blog/video/list/", "Video"),
            (f"{base_url}/blog/video/upload/", "Upload Video"),
            (f"{base_url}/blog/gallery/", "Gallery"),
            (f"{base_url}/blog/album/", "Album"),
            (f"{base_url}/users/login/", "Login"),
            (f"{base_url}/users/register/", "Register"),
            (f"{base_url}/secure-console-7f9a2c-admin/", "Admin"),
        ]
        return format_html(
            '<div style="max-width: 980px; line-height: 1.8;">{}</div>',
            format_html_join(
                "",
                '<a href="{}">{}</a><span style="color:#9ca3af;"> | </span>',
                links,
            ),
        )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        site = Site.objects.order_by("id").first()
        route_links = []
        if site:
            base_url = f"http://{site.domain}".rstrip("/")
            route_specs = [
                ("Home", "/"),
                ("Blog", "/blog/"),
                ("Create Post", "/blog/create/"),
                ("Search Posts", "/blog/search/"),
                ("Audio List", "/blog/audio/list/"),
                ("Upload Audio", "/blog/audio/upload/"),
                ("Video List", "/blog/video/list/"),
                ("Upload Video", "/blog/video/upload/"),
                ("Gallery", "/blog/gallery/"),
                ("Upload Gallery", "/blog/gallery/upload/"),
                ("Album", "/blog/album/"),
                ("Upload Album", "/blog/album/upload/"),
                ("Login", "/users/login/"),
                ("Register", "/users/register/"),
                ("Profile", "/users/profile/"),
                ("Admin", "/secure-console-7f9a2c-admin/"),
            ]
            route_links = [
                {"id": index, "label": label, "url": f"{base_url}{path}"}
                for index, (label, path) in enumerate(route_specs, start=1)
            ]
        extra_context["route_links"] = route_links
        extra_context["template_links"] = _template_inventory()
        return super().changelist_view(request, extra_context=extra_context)

    def has_delete_permission(self, request, obj=None):
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "template-preview/",
                self.admin_site.admin_view(self.template_preview_view),
                name="sites_site_template_preview",
            ),
        ]
        return custom_urls + urls

    def template_preview_view(self, request):
        relative_path = request.GET.get("path", "").strip()
        base_dir = Path(settings.BASE_DIR)
        target = (base_dir / relative_path).resolve()
        allowed_roots = [
            (base_dir / "blog" / "templates").resolve(),
            (base_dir / "images" / "templates").resolve(),
            (base_dir / "my_site" / "templates").resolve(),
        ]
        if not relative_path or not any(str(target).startswith(str(root)) for root in allowed_roots) or not target.exists():
            context = {
                **self.admin_site.each_context(request),
                "title": "Template Preview",
                "subtitle": "Invalid template path",
                "template_path": relative_path,
                "template_source": "Template not found.",
            }
            return TemplateResponse(request, "admin/sites/site/template_preview.html", context, status=404)

        context = {
            **self.admin_site.each_context(request),
            "title": "Template Preview",
            "subtitle": target.name,
            "template_path": relative_path,
            "template_source": target.read_text(encoding="utf-8", errors="replace"),
        }
        return TemplateResponse(request, "admin/sites/site/template_preview.html", context)

    @admin.display(description="Available Pages")
    def site_links(self, obj):
        base_url = f"http://{obj.domain}".rstrip("/")
        links = [
            (f"{base_url}/", "Home"),
            (f"{base_url}/blog/", "Blog"),
            (f"{base_url}/blog/create/", "Create Post"),
            (f"{base_url}/blog/search/", "Search Posts"),
            (f"{base_url}/blog/audio/list/", "Audio List"),
            (f"{base_url}/blog/audio/upload/", "Upload Audio"),
            (f"{base_url}/blog/video/list/", "Video List"),
            (f"{base_url}/blog/video/upload/", "Upload Video"),
            (f"{base_url}/blog/gallery/", "Gallery"),
            (f"{base_url}/blog/gallery/upload/", "Upload Gallery"),
            (f"{base_url}/blog/album/", "Album"),
            (f"{base_url}/blog/album/upload/", "Upload Album"),
            (f"{base_url}/users/login/", "Login"),
            (f"{base_url}/users/register/", "Register"),
            (f"{base_url}/users/profile/", "Profile"),
            (f"{base_url}/secure-console-7f9a2c-admin/", "Admin"),
        ]
        return format_html(
            '<div style="max-width: 980px; padding: 12px 0;"><ul style="margin: 0; padding-left: 18px;">{}</ul></div>',
            format_html_join(
                "",
                '<li><a href="{}">{}</a></li>',
                links,
            ),
        )


@admin.register(AudioPost)
class AudioPostAdmin(admin.ModelAdmin):
    list_display = [
        "music_name",
        "uploaded_by",
        "created",
        "updated",
        "active",
    ]
    fields = ["music_name", "audio_file", "description", "uploaded_by", "active", "created", "updated"]
    list_filter = ["active", "created", "updated", "uploaded_by"]
    search_fields = ["music_name", "description", "uploaded_by__username"]
    readonly_fields = ["created", "updated"]
    raw_id_fields = ["uploaded_by"]
    autocomplete_fields = ["uploaded_by"]
    ordering = ["-created"]
    list_per_page = 20
    date_hierarchy = "created"
    actions = [make_active, make_inactive]
    show_facets = admin.ShowFacets.ALWAYS

    @admin.display(description="Audio Preview")
    def audio_preview(self, obj):
        if not obj.audio_file:
            return "-"
        return format_html(
            '<audio controls preload="metadata" style="width: 220px;"><source src="{}"></audio>',
            obj.get_audio_proxy_url(),
        )

    @admin.display(description="Cover Preview")
    def cover_preview(self, obj):
        if not obj.cover_image:
            return "-"
        return format_html(
            '<img src="{}" alt="cover" style="width: 56px; height: 56px; object-fit: cover; border-radius: 6px;" />',
            obj.get_cover_image_proxy_url(),
        )


@admin.register(VideoPost)
class VideoPostAdmin(admin.ModelAdmin):
    list_display = ["title", "uploaded_by", "created", "updated"]
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
    list_display = ["timestamp", "method", "path_preview", "status_code", "user", "ip_address", "response_time"]
    list_filter = ["method", "status_code"]
    search_fields = ["path", "ip_address", "user__username"]
    readonly_fields = ["user", "method", "path", "ip_address", "status_code", "response_time", "timestamp"]
    list_per_page = 50
    date_hierarchy = "timestamp"
    ordering = ["-timestamp"]
    list_select_related = ["user"]
    show_full_result_count = False
    show_facets = admin.ShowFacets.NEVER
    list_max_show_all = 200

    @admin.display(description="Path", ordering="path")
    def path_preview(self, obj):
        path = (obj.path or "").strip()
        return f"{path[:90]}..." if len(path) > 90 else path

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["system_status_url"] = reverse("admin:system_status")
        return super().changelist_view(request, extra_context=extra_context)
