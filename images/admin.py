from django.contrib import admin
from django.core.cache import cache
from django.db.models import Prefetch
from django.utils.html import format_html, format_html_join

from .forms import ImagePostForm
from .models import Album, AlbumImage, ImagePost


ADMIN_CACHE_TTL = 60 * 60 * 24 * 30


def _album_preview_cache_key(prefix, obj, images):
    latest_image_stamp = max(
        int((image.updated or image.created).timestamp()) if (image.updated or image.created) else image.pk
        for image in images
    )
    album_stamp = int((obj.updated or obj.created).timestamp()) if (obj.updated or obj.created) else obj.pk
    return f"admin:{prefix}:album:{obj.pk}:album:{album_stamp}:images:{len(images)}:{latest_image_stamp}"


class AlbumImageInline(admin.TabularInline):
    model = AlbumImage
    extra = 0
    fields = ["title", "uploaded_by", "created"]
    readonly_fields = ["created"]
    autocomplete_fields = ["uploaded_by"]
    show_change_link = True

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("uploaded_by")


@admin.register(ImagePost)
class ImageAdmin(admin.ModelAdmin):
    form = ImagePostForm
    list_display = ["title", "uploaded_by", "created", "updated"]
    list_filter = ["created", "updated", "uploaded_by"]
    search_fields = ["title", "description", "uploaded_by__username"]
    readonly_fields = ["thumbnail_preview", "created", "updated"]
    fields = ["title", "image", "thumbnail_preview", "description", "uploaded_by", "created", "updated"]
    raw_id_fields = ["uploaded_by"]
    autocomplete_fields = ["uploaded_by"]
    ordering = ["-created"]
    list_per_page = 20
    date_hierarchy = "created"
    show_facets = admin.ShowFacets.NEVER

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("uploaded_by")

    @admin.display(description="Thumbnail")
    def thumbnail_preview(self, obj):
        if not obj.image:
            return "-"
        return format_html(
            '<img src="{}" alt="image" loading="lazy" decoding="async" style="width:56px; height:56px; object-fit:cover; border-radius:6px;" />',
            obj.get_image_proxy_url(),
        )


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ["title", "uploaded_by", "image_count", "created", "updated"]
    list_filter = ["created", "updated", "uploaded_by"]
    search_fields = ["title", "description", "uploaded_by__username"]
    readonly_fields = ["cover_preview", "gallery_preview", "created", "updated"]
    fields = ["title", "cover_preview", "gallery_preview", "description", "uploaded_by", "created", "updated"]
    raw_id_fields = ["uploaded_by"]
    autocomplete_fields = ["uploaded_by"]
    ordering = ["-created"]
    list_per_page = 20
    date_hierarchy = "created"
    show_facets = admin.ShowFacets.NEVER
    inlines = [AlbumImageInline]

    def get_queryset(self, request):
        image_queryset = AlbumImage.objects.select_related("uploaded_by").only(
            "id",
            "album_id",
            "title",
            "image",
            "created",
            "updated",
            "uploaded_by__username",
        ).order_by("created", "id")
        return super().get_queryset(request).select_related("uploaded_by").prefetch_related(
            Prefetch("images", queryset=image_queryset)
        )

    def _album_images(self, obj):
        prefetched = getattr(obj, "_prefetched_objects_cache", {}).get("images")
        if prefetched is not None:
            return [image for image in prefetched if image.image]
        return [image for image in obj.images.order_by("created", "id") if image.image]

    @admin.display(description="Cover")
    def cover_preview(self, obj):
        images = self._album_images(obj)
        if not images:
            return "-"
        cache_key = _album_preview_cache_key("cover", obj, images)
        cached_html = cache.get(cache_key)
        if cached_html is not None:
            return cached_html
        first_image = images[0]
        html = format_html(
            '<img src="{}" alt="album cover" loading="eager" decoding="async" style="width:72px; height:72px; object-fit:cover; border-radius:8px;" />',
            first_image.get_image_proxy_url(),
        )
        cache.set(cache_key, html, ADMIN_CACHE_TTL)
        return html

    @admin.display(description="Album Images")
    def gallery_preview(self, obj):
        images = self._album_images(obj)
        if not images:
            return "No images in this album."
        cache_key = _album_preview_cache_key("gallery", obj, images)
        cached_html = cache.get(cache_key)
        if cached_html is not None:
            return cached_html
        items = [(image.get_image_proxy_url(), image.get_image_proxy_url(), image.title or f"Image {image.pk}") for image in images]
        html = format_html(
            '<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:12px; max-width:960px;">{}</div>',
            format_html_join(
                "",
                '<a href="{}" target="_blank" rel="noopener" style="display:flex; flex-direction:column; gap:8px; text-decoration:none;"><img src="{}" alt="{}" loading="lazy" decoding="async" fetchpriority="low" style="width:100%; height:120px; object-fit:cover; border-radius:8px; border:1px solid #d1d5db;" /><span style="font-size:12px; color:#374151; word-break:break-word;">{}</span></a>',
                [(href, src, label, label) for href, src, label in items],
            ),
        )
        cache.set(cache_key, html, ADMIN_CACHE_TTL)
        return html


@admin.register(AlbumImage)
class AlbumImageAdmin(admin.ModelAdmin):
    list_display = ["title", "album", "uploaded_by", "created", "updated"]
    list_filter = ["created", "updated", "uploaded_by", "album"]
    search_fields = ["title", "description", "album__title", "uploaded_by__username"]
    readonly_fields = ["thumbnail_preview", "created", "updated"]
    raw_id_fields = ["album", "uploaded_by"]
    autocomplete_fields = ["album", "uploaded_by"]
    ordering = ["album", "created", "id"]
    list_per_page = 30
    date_hierarchy = "created"
    show_facets = admin.ShowFacets.NEVER

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("album", "uploaded_by")

    @admin.display(description="Thumbnail")
    def thumbnail_preview(self, obj):
        if not obj.image:
            return "-"
        return format_html(
            '<img src="{}" alt="image" loading="lazy" decoding="async" style="width:56px; height:56px; object-fit:cover; border-radius:6px;" />',
            obj.get_image_proxy_url(),
        )
