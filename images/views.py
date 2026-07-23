import mimetypes
import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.http import FileResponse, Http404, HttpResponse, HttpResponseNotModified
from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse
from django.utils.http import http_date, parse_http_date_safe, quote_etag

from blog.models import Post

from .forms import AlbumEditForm, AlbumImageEditForm, AlbumUploadForm, GalleryImageEditForm, GallerySingleUploadForm
from .models import Album, AlbumImage, ImagePost
from my_site.media_helpers import filter_existing_media_instances, invalidate_cache_keys, invalidate_public_view_caches, media_file_exists, prime_id_cache
from my_site.site_views import queue_operation_success, render_public_cached_template
from my_site.sorting import build_sort_context


PUBLIC_GALLERY_HTML_CACHE_TTL = 60 * 60 * 24 * 30


def _render_public_cached_template(request, cache_key, template_name, context, timeout=PUBLIC_GALLERY_HTML_CACHE_TTL):
    return render_public_cached_template(request, cache_key, template_name, context, timeout=timeout)


def _invalidate_image_public_views():
    invalidate_public_view_caches(
        "view:site_index",
        "view:gallery_list:page:1",
        "view:album_list:page:1",
    )



def album_list(request):
    sort_context = build_sort_context(
        request,
        {
            "newest": "Newest",
            "oldest": "Oldest",
            "title_az": "Title A-Z",
            "title_za": "Title Z-A",
            "most_items": "Most Images",
            "fewest_items": "Fewest Images",
        },
        default_sort="newest",
    )
    album_ids = cache.get("album_list:valid_album_ids")
    if album_ids is None:
        album_queryset = Album.objects.select_related("uploaded_by").prefetch_related("images").order_by("-created")
        album_ids = [
            album.id
            for album in album_queryset
            if any(media_file_exists(image.image) for image in album.images.all())
        ]
        cache.set("album_list:valid_album_ids", album_ids, 300)
    album_map = {
        album.id: album
        for album in Album.objects.select_related("uploaded_by").prefetch_related("images").filter(id__in=album_ids)
    }
    albums = [album_map[album_id] for album_id in album_ids if album_id in album_map]
    if sort_context["selected_sort"] == "oldest":
        albums.sort(key=lambda album: (album.created, album.id))
    elif sort_context["selected_sort"] == "title_az":
        albums.sort(key=lambda album: ((album.title or "").lower(), -album.id))
    elif sort_context["selected_sort"] == "title_za":
        albums.sort(key=lambda album: ((album.title or "").lower(), -album.id), reverse=True)
    elif sort_context["selected_sort"] == "most_items":
        albums.sort(key=lambda album: (album.image_count, album.created, album.id), reverse=True)
    elif sort_context["selected_sort"] == "fewest_items":
        albums.sort(key=lambda album: (album.image_count, album.created, album.id))
    paginator = Paginator(albums, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    context = {"albums": page_obj.object_list, "page_obj": page_obj, "total_albums": len(albums), **sort_context}
    cache_key = f"view:album_list:page:{request.GET.get('page', 1)}:sort:{sort_context['selected_sort']}"
    return _render_public_cached_template(request, cache_key, "images/album_list.html", context)


@login_required
def album_upload(request):
    if request.method == "POST":
        form = AlbumUploadForm(request.POST, request.FILES)
        try:
            uploads = form.extract_uploads()
            description = request.POST.get("description", "")
            first_title = form.build_title(image=uploads[0], index=1)
            album = Album.objects.create(
                title=first_title if len(uploads) == 1 else f"{first_title} and {len(uploads) - 1} more",
                description=description,
                uploaded_by=request.user,
            )

            for index, image in enumerate(uploads, start=1):
                album_image = AlbumImage(
                    album=album,
                    title=form.build_title(image=image, index=index),
                    description=description,
                    uploaded_by=request.user,
                )
                album_image.image = image
                album_image.save()

            invalidate_cache_keys("album_list:valid_album_ids")
            _invalidate_image_public_views()
            messages.success(request, f"Album created successfully. {len(uploads)} image(s) were added.")
            return queue_operation_success(
                request,
                title="Album Created",
                message=f"Album created successfully. {len(uploads)} image(s) were added.",
                primary_label="Open Album",
                primary_url=redirect("blog:images:album_detail", image_id=album.id).url,
                secondary_label="Album List",
                secondary_url=redirect("blog:images:album_list").url,
            )
        except ValidationError as exc:
            form.add_error("images", exc)
    else:
        form = AlbumUploadForm()

    return render(request, "images/album_upload.html", {"form": form})


def album_detail(request, image_id):
    album = get_object_or_404(Album.objects.select_related("uploaded_by").prefetch_related("images"), pk=image_id)
    images = filter_existing_media_instances(album.images.all(), "image")
    if not images:
        messages.error(request, "Album images are missing.")
        return redirect("blog:images:album_list")

    can_manage = request.user.is_authenticated and (
        album.uploaded_by_id == request.user.id or request.user.is_superuser
    )
    return render(
        request,
        "images/album_detail.html",
        {"album": album, "images": images, "can_manage": can_manage},
    )


@login_required
def album_edit(request, image_id):
    album = get_object_or_404(Album, pk=image_id)
    if album.uploaded_by_id != request.user.id and not request.user.is_superuser:
        messages.error(request, "Permission denied for editing this album.")
        return redirect("blog:images:album_detail", image_id=album.id)

    if request.method == "POST":
        form = AlbumEditForm(request.POST, instance=album)
        if form.is_valid():
            form.save()
            invalidate_cache_keys("album_list:valid_album_ids")
            _invalidate_image_public_views()
            messages.success(request, "Album details updated.")
            return queue_operation_success(
                request,
                title="Album Updated",
                message="Album details were updated successfully.",
                primary_label="View Album",
                primary_url=redirect("blog:images:album_detail", image_id=album.id).url,
                secondary_label="Album List",
                secondary_url=redirect("blog:images:album_list").url,
            )
    else:
        form = AlbumEditForm(instance=album)

    return render(request, "images/album_edit.html", {"form": form, "album": album})


@login_required
def album_delete(request, image_id):
    album = get_object_or_404(Album.objects.prefetch_related("images"), pk=image_id)
    if album.uploaded_by_id != request.user.id and not request.user.is_superuser:
        messages.error(request, "Permission denied for deleting this album.")
        return redirect("blog:images:album_detail", image_id=album.id)

    if request.method == "POST":
        album.delete()
        invalidate_cache_keys("album_list:valid_album_ids")
        _invalidate_image_public_views()
        messages.success(request, "Album deleted.")
        return queue_operation_success(
            request,
            title="Album Deleted",
            message="The album was deleted successfully.",
            primary_label="Open Album List",
            primary_url=redirect("blog:images:album_list").url,
        )

    return render(request, "images/album_delete_confirm.html", {"album": album})


def album_media(request, image_id):
    image = get_object_or_404(AlbumImage.objects.select_related("uploaded_by", "album"), pk=image_id)
    if not image.image:
        raise Http404("Image file is missing.")
    try:
        file_path = image.image.path
        file_name = image.image.name.rsplit("/", 1)[-1]
        content_type, _ = mimetypes.guess_type(file_name)
        stat_result = os.stat(file_path)
        last_modified = stat_result.st_mtime
        etag = quote_etag(f"album-{image.pk}-{int(last_modified)}-{stat_result.st_size}")

        if_none_match = request.headers.get("If-None-Match")
        if if_none_match and if_none_match == etag:
            response = HttpResponseNotModified()
        else:
            if_modified_since = parse_http_date_safe(request.headers.get("If-Modified-Since", ""))
            if if_modified_since and int(last_modified) <= if_modified_since:
                response = HttpResponseNotModified()
            else:
                response = FileResponse(
                    open(file_path, "rb"),
                    content_type=content_type or "application/octet-stream",
                    headers={"Content-Disposition": f'inline; filename="{file_name}"'},
                )

        response["Cache-Control"] = "public, max-age=604800"
        response["ETag"] = etag
        response["Last-Modified"] = http_date(last_modified)
        return response
    except OSError as exc:
        raise Http404("Image file is missing.") from exc


def _prime_gallery_list_cache(new_items=None):
    return prime_id_cache(
        "gallery_list:valid_image_ids",
        ImagePost.objects.select_related("uploaded_by"),
        "image",
        new_items=new_items,
    )


def gallery_list(request):
    sort_context = build_sort_context(
        request,
        {
            "newest": "Newest",
            "oldest": "Oldest",
            "title_az": "Title A-Z",
            "title_za": "Title Z-A",
        },
        default_sort="newest",
    )
    image_ids = cache.get("gallery_list:valid_image_ids")
    if image_ids is None:
        image_ids = _prime_gallery_list_cache()
    image_map = {
        image.id: image
        for image in ImagePost.objects.select_related("uploaded_by").filter(id__in=image_ids)
    }
    images = [image_map[image_id] for image_id in image_ids if image_id in image_map]
    if sort_context["selected_sort"] == "oldest":
        images.sort(key=lambda image: (image.created, image.id))
    elif sort_context["selected_sort"] == "title_az":
        images.sort(key=lambda image: ((image.title or "").lower(), -image.id))
    elif sort_context["selected_sort"] == "title_za":
        images.sort(key=lambda image: ((image.title or "").lower(), -image.id), reverse=True)
    paginator = Paginator(images, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    context = {"images": page_obj.object_list, "page_obj": page_obj, **sort_context}
    cache_key = f"view:gallery_list:page:{request.GET.get('page', 1)}:sort:{sort_context['selected_sort']}"
    return _render_public_cached_template(request, cache_key, "images/gallery_list.html", context)


def gallery_detail(request, image_id):
    image = get_object_or_404(ImagePost.objects.select_related("uploaded_by"), pk=image_id)
    if not media_file_exists(image.image):
        messages.error(request, "Image file is missing.")
        return redirect("blog:images:gallery_list")

    linked_post = None
    if image.image and image.image.name:
        linked_post = (
            Post.published.filter(cover_image=image.image.name)
            .select_related("author")
            .order_by("-publish", "-id")
            .first()
        )

    can_manage = request.user.is_authenticated and (
        image.uploaded_by_id == request.user.id or request.user.is_superuser
    )
    return render(
        request,
        "images/gallery_detail.html",
        {"image": image, "can_manage": can_manage, "linked_post": linked_post},
    )


@login_required
def gallery_upload(request):
    if request.method == "POST":
        form = GallerySingleUploadForm(request.POST, request.FILES)
        try:
            uploads = form.extract_uploads()
            description = request.POST.get("description", "")
            created_count = 0

            created_images = []
            for index, image in enumerate(uploads, start=1):
                image_post = ImagePost(
                    title=form.build_title(image=image, index=index),
                    description=description,
                    uploaded_by=request.user,
                )
                image_post.image = image
                image_post.save()
                created_images.append(image_post)
                created_count += 1

            _prime_gallery_list_cache()
            _invalidate_image_public_views()
            messages.success(request, "Image uploaded successfully. It is now available in Gallery.")
            return queue_operation_success(
                request,
                title="Image Uploaded",
                message="Image uploaded successfully. It is now available in Gallery.",
                primary_label="Open Gallery",
                primary_url=redirect("blog:images:gallery_list").url,
            )
        except ValidationError as exc:
            form.add_error("images", exc)
    else:
        form = GallerySingleUploadForm()

    return render(request, "images/gallery_upload.html", {"form": form})


@login_required
def gallery_delete(request, image_id):
    image = get_object_or_404(ImagePost, pk=image_id)
    if image.uploaded_by_id != request.user.id and not request.user.is_superuser:
        messages.error(request, "Permission denied for deleting this image.")
        return redirect("blog:images:gallery_detail", image_id=image.id)

    if request.method == "POST":
        image.delete()
        _invalidate_image_public_views()
        messages.success(request, "Image deleted.")
        return queue_operation_success(
            request,
            title="Image Deleted",
            message="The image was deleted successfully.",
            primary_label="Open Gallery",
            primary_url=redirect("blog:images:gallery_list").url,
        )

    return render(request, "images/gallery_delete_confirm.html", {"image": image})


@login_required
def gallery_edit(request, image_id):
    image = get_object_or_404(ImagePost, pk=image_id)
    if image.uploaded_by_id != request.user.id and not request.user.is_superuser:
        messages.error(request, "Permission denied for editing this image.")
        return redirect("blog:images:gallery_detail", image_id=image.id)

    if request.method == "POST":
        form = GalleryImageEditForm(request.POST, instance=image)
        if form.is_valid():
            form.save()
            _invalidate_image_public_views()
            messages.success(request, "Image details updated.")
            return queue_operation_success(
                request,
                title="Image Updated",
                message="Image details were updated successfully.",
                primary_label="View Image",
                primary_url=redirect("blog:images:gallery_detail", image_id=image.id).url,
                secondary_label="Open Gallery",
                secondary_url=redirect("blog:images:gallery_list").url,
            )
    else:
        form = GalleryImageEditForm(instance=image)

    return render(request, "images/gallery_edit.html", {"form": form, "image": image})


def gallery_media(request, image_id):
    image = get_object_or_404(ImagePost.objects.select_related("uploaded_by"), pk=image_id)
    if not image.image:
        raise Http404("Image file is missing.")
    try:
        file_path = image.image.path
        file_name = image.image.name.rsplit("/", 1)[-1]
        content_type, _ = mimetypes.guess_type(file_name)
        stat_result = os.stat(file_path)
        last_modified = stat_result.st_mtime
        etag = quote_etag(f"gallery-{image.pk}-{int(last_modified)}-{stat_result.st_size}")

        if_none_match = request.headers.get("If-None-Match")
        if if_none_match and if_none_match == etag:
            response = HttpResponseNotModified()
        else:
            if_modified_since = parse_http_date_safe(request.headers.get("If-Modified-Since", ""))
            if if_modified_since and int(last_modified) <= if_modified_since:
                response = HttpResponseNotModified()
            else:
                response = FileResponse(
                    open(file_path, "rb"),
                    content_type=content_type or "application/octet-stream",
                    headers={"Content-Disposition": f'inline; filename="{file_name}"'},
                )

        response["Cache-Control"] = "public, max-age=604800"
        response["ETag"] = etag
        response["Last-Modified"] = http_date(last_modified)
        return response
    except OSError as exc:
        raise Http404("Image file is missing.") from exc
