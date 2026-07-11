from django.contrib import admin
from django.utils.html import format_html

from .forms import ImagePostForm
from .models import Album, AlbumImage, ImagePost


class AlbumImageInline(admin.TabularInline):
    model = AlbumImage
    extra = 0
    fields = ["preview", "title", "uploaded_by", "created"]
    readonly_fields = ["preview", "created"]
    autocomplete_fields = ["uploaded_by"]
    show_change_link = True

    @admin.display(description="Preview")
    def preview(self, obj):
        if not obj.pk or not obj.image:
            return "-"
        return format_html(
            '<img src="{}" alt="image" style="width: 56px; height: 56px; object-fit: cover; border-radius: 6px;" />',
            obj.get_image_proxy_url(),
        )


@admin.register(ImagePost)
class ImageAdmin(admin.ModelAdmin):
    form = ImagePostForm
    list_display = ["thumbnail_preview", "title", "uploaded_by", "created", "updated"]
    list_filter = ["created", "updated", "uploaded_by"]
    search_fields = ["title", "description", "uploaded_by__username"]
    readonly_fields = ["thumbnail_preview", "created", "updated"]
    raw_id_fields = ["uploaded_by"]
    autocomplete_fields = ["uploaded_by"]
    ordering = ["-created"]
    list_per_page = 20
    date_hierarchy = "created"
    show_facets = admin.ShowFacets.ALWAYS

    @admin.display(description="Thumbnail")
    def thumbnail_preview(self, obj):
        if not obj.image:
            return "-"
        return format_html(
            '<img src="{}" alt="image" style="width: 56px; height: 56px; object-fit: cover; border-radius: 6px;" />',
            obj.get_image_proxy_url(),
        )


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ["cover_preview", "title", "uploaded_by", "image_count", "created", "updated"]
    list_filter = ["created", "updated", "uploaded_by"]
    search_fields = ["title", "description", "uploaded_by__username"]
    readonly_fields = ["cover_preview", "created", "updated"]
    raw_id_fields = ["uploaded_by"]
    autocomplete_fields = ["uploaded_by"]
    ordering = ["-created"]
    list_per_page = 20
    date_hierarchy = "created"
    show_facets = admin.ShowFacets.ALWAYS
    inlines = [AlbumImageInline]

    @admin.display(description="Cover")
    def cover_preview(self, obj):
        cover = obj.cover_image()
        if not cover or not cover.image:
            return "-"
        return format_html(
            '<img src="{}" alt="cover" style="width: 56px; height: 56px; object-fit: cover; border-radius: 6px;" />',
            cover.get_image_proxy_url(),
        )


@admin.register(AlbumImage)
class AlbumImageAdmin(admin.ModelAdmin):
    list_display = ["thumbnail_preview", "title", "album", "uploaded_by", "created", "updated"]
    list_filter = ["created", "updated", "uploaded_by", "album"]
    search_fields = ["title", "description", "album__title", "uploaded_by__username"]
    readonly_fields = ["thumbnail_preview", "created", "updated"]
    raw_id_fields = ["album", "uploaded_by"]
    autocomplete_fields = ["album", "uploaded_by"]
    ordering = ["album", "created", "id"]
    list_per_page = 30
    date_hierarchy = "created"
    show_facets = admin.ShowFacets.ALWAYS

    @admin.display(description="Thumbnail")
    def thumbnail_preview(self, obj):
        if not obj.image:
            return "-"
        return format_html(
            '<img src="{}" alt="image" style="width: 56px; height: 56px; object-fit: cover; border-radius: 6px;" />',
            obj.get_image_proxy_url(),
        )
