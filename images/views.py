import mimetypes

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy

from blog.models import Post

from .forms import AlbumUploadForm, GalleryImageEditForm, GalleryUploadForm
from .models import Album, AlbumImage, ImagePost
from my_site.media_sync import maybe_sync_site_media
from my_site.site_views import queue_operation_success


def _is_post_request(request):
    return request.method == "POST"


def _has_image_file(image):
    return bool(image and default_storage.exists(image.name))


def _redirect_to_gallery_detail(image_id):
    return redirect("blog:images:gallery_detail", image_id=image_id)


def _disable_page_cache(response):
    response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response


def _build_sort_options(current_sort):
    options = [
        ("newest", "Newest"),
        ("oldest", "Oldest"),
        ("title_asc", "A-Z"),
        ("title_desc", "Z-A"),
        ("updated", "Updated"),
        ("author", "Author"),
    ]
    return [
        {
            "label": label,
            "url": f"?sort={value}",
            "active": current_sort == value,
        }
        for value, label in options
    ]



def gallery_list(request):
    maybe_sync_site_media()
    sort = request.GET.get("sort", "newest")
    sort_map = {
        "newest": ["-created", "-id"],
        "oldest": ["created", "id"],
        "title_asc": ["title", "id"],
        "title_desc": ["-title", "-id"],
        "updated": ["-updated", "-id"],
        "author": ["uploaded_by__username", "title", "id"],
    }
    current_sort = sort if sort in sort_map else "newest"
    images = [
        image
        for image in ImagePost.objects.select_related("uploaded_by").order_by(*sort_map[current_sort])
        if _has_image_file(image.image)
    ]
    paginator = Paginator(images, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    response = render(
        request,
        "images/gallery_list.html",
        {
            "images": page_obj.object_list,
            "page_obj": page_obj,
            "current_sort": current_sort,
            "sort_options": _build_sort_options(current_sort),
        },
    )
    return _disable_page_cache(response)


def gallery_detail(request, image_id):
    maybe_sync_site_media()
    image = get_object_or_404(ImagePost.objects.select_related("uploaded_by"), pk=image_id)
    if not _has_image_file(image.image):
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
    response = render(
        request,
        "images/gallery_detail.html",
        {"image": image, "can_manage": can_manage, "linked_post": linked_post},
    )
    return _disable_page_cache(response)


@login_required
def gallery_upload(request):
    form = GalleryUploadForm(request.POST or None, request.FILES or None)
    if _is_post_request(request):
        try:
            uploads = form.extract_uploads()
            description = request.POST.get("description", "")
            created_count = 0

            for index, image in enumerate(uploads, start=1):
                image_post = ImagePost(
                    title=form.build_title(image=image, index=index),
                    description=description,
                    uploaded_by=request.user,
                )
                image_post.image = image
                image_post.save()
                created_count += 1

            return queue_operation_success(
                request,
                title="Gallery Upload Complete",
                message=f"{created_count} image(s) have been uploaded to the gallery.",
                primary_label="Open Gallery",
                primary_url=reverse_lazy("blog:images:gallery_list"),
                secondary_label="Upload More Images",
                secondary_url=reverse_lazy("blog:images:gallery_upload"),
            )
        except ValidationError as exc:
            form.add_error("images", exc)

    response = render(request, "images/gallery_upload.html", {"form": form})
    return _disable_page_cache(response)


@login_required
def gallery_delete(request, image_id):
    image = get_object_or_404(ImagePost, pk=image_id)
    if image.uploaded_by_id != request.user.id and not request.user.is_superuser:
        messages.error(request, "You do not have permission to delete this image.")
        return _redirect_to_gallery_detail(image.id)

    if _is_post_request(request):
        image_title = image.title
        image.delete()
        return queue_operation_success(
            request,
            title="Gallery Image Deleted",
            message=f'"{image_title}" has been deleted successfully.',
            primary_label="Open Gallery",
            primary_url=reverse_lazy("blog:images:gallery_list"),
            secondary_label="Upload More Images",
            secondary_url=reverse_lazy("blog:images:gallery_upload"),
        )

    response = render(request, "images/gallery_delete_confirm.html", {"image": image})
    return _disable_page_cache(response)


@login_required
def gallery_edit(request, image_id):
    image = get_object_or_404(ImagePost, pk=image_id)
    if image.uploaded_by_id != request.user.id and not request.user.is_superuser:
        messages.error(request, "You do not have permission to edit this image.")
        return _redirect_to_gallery_detail(image.id)

    form = GalleryImageEditForm(request.POST or None, instance=image)
    if _is_post_request(request) and form.is_valid():
        form.save()
        return queue_operation_success(
            request,
            title="Gallery Image Updated",
            message=f'"{image.title}" has been updated successfully.',
            primary_label="View Image",
            primary_url=reverse_lazy("blog:images:gallery_detail", kwargs={"image_id": image.id}),
            secondary_label="Open Gallery",
            secondary_url=reverse_lazy("blog:images:gallery_list"),
        )

    response = render(request, "images/gallery_edit.html", {"form": form, "image": image})
    return _disable_page_cache(response)


def gallery_media(request, image_id):
    image = get_object_or_404(ImagePost.objects.select_related("uploaded_by"), pk=image_id)
    if not image.image:
        raise Http404("Image file is missing.")
    try:
        file_path = image.image.path
        file_name = image.image.name.rsplit("/", 1)[-1]
        content_type, _ = mimetypes.guess_type(file_name)
        return FileResponse(
            open(file_path, "rb"),
            content_type=content_type or "application/octet-stream",
            headers={
                "Content-Disposition": f'inline; filename="{file_name}"',
                "Cache-Control": "public, max-age=7776000, immutable",
            },
        )
    except OSError as exc:
        raise Http404("Image file is missing.") from exc

def album_list(request):
    maybe_sync_site_media()
    sort = request.GET.get("sort", "newest")
    sort_map = {
        "newest": ["-created", "-id"],
        "oldest": ["created", "id"],
        "title_asc": ["title", "id"],
        "title_desc": ["-title", "-id"],
        "updated": ["-updated", "-id"],
        "author": ["uploaded_by__username", "title", "id"],
    }
    current_sort = sort if sort in sort_map else "newest"
    albums = Album.objects.select_related("uploaded_by").prefetch_related("images").order_by(*sort_map[current_sort])
    paginator = Paginator(albums, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    response = render(
        request,
        "images/album_list.html",
        {
            "albums": page_obj.object_list,
            "page_obj": page_obj,
            "current_sort": current_sort,
            "sort_options": _build_sort_options(current_sort),
            "pagination_suffix": f"?sort={current_sort}",
        },
    )
    return _disable_page_cache(response)


def album_detail(request, image_id):
    maybe_sync_site_media()
    album = get_object_or_404(Album.objects.select_related("uploaded_by").prefetch_related("images__uploaded_by"), pk=image_id)
    images = [image for image in album.images.all() if _has_image_file(image.image)]
    can_manage = request.user.is_authenticated and (
        album.uploaded_by_id == request.user.id or request.user.is_superuser
    )
    response = render(
        request,
        "images/album_detail.html",
        {"album": album, "images": images, "can_manage": can_manage},
    )
    return _disable_page_cache(response)


@login_required
def album_upload(request):
    form = AlbumUploadForm(request.POST or None, request.FILES or None)
    if _is_post_request(request) and form.is_valid():
        album = Album.objects.create(
            title=form.cleaned_data["title"],
            description=form.cleaned_data.get("description", ""),
            uploaded_by=request.user,
        )
        for index, image in enumerate(form.cleaned_data["images"], start=1):
            AlbumImage.objects.create(
                album=album,
                title=f"{album.title} {index}",
                image=image,
                description=album.description,
                uploaded_by=request.user,
            )
        return queue_operation_success(
            request,
            title="Album Created",
            message=f'"{album.title}" has been created successfully.',
            primary_label="View Album",
            primary_url=reverse_lazy("blog:images:album_detail", kwargs={"image_id": album.id}),
            secondary_label="Open Albums",
            secondary_url=reverse_lazy("blog:images:album_list"),
        )

    response = render(request, "images/album_upload.html", {"form": form})
    return _disable_page_cache(response)


@login_required
def album_delete(request, image_id):
    album = get_object_or_404(Album.objects.prefetch_related("images"), pk=image_id)
    if album.uploaded_by_id != request.user.id and not request.user.is_superuser:
        messages.error(request, "You do not have permission to delete this album.")
        return redirect("blog:images:album_detail", image_id=album.id)

    if _is_post_request(request):
        album_title = album.title
        album.delete()
        return queue_operation_success(
            request,
            title="Album Deleted",
            message=f'"{album_title}" and its images have been deleted successfully.',
            primary_label="Open Albums",
            primary_url=reverse_lazy("blog:images:album_list"),
            secondary_label="Create New Album",
            secondary_url=reverse_lazy("blog:images:album_upload"),
        )

    response = render(request, "images/album_delete_confirm.html", {"album": album})
    return _disable_page_cache(response)


@login_required
def album_edit(request, image_id):
    messages.info(request, "Album edit page is not fully restored yet.")
    return redirect("blog:images:album_detail", image_id=image_id)


def album_media(request, image_id):
    image = get_object_or_404(AlbumImage.objects.select_related("uploaded_by", "album"), pk=image_id)
    if not image.image:
        raise Http404("Image file is missing.")
    try:
        file_path = image.image.path
        file_name = image.image.name.rsplit("/", 1)[-1]
        content_type, _ = mimetypes.guess_type(file_name)
        return FileResponse(
            open(file_path, "rb"),
            content_type=content_type or "application/octet-stream",
            headers={"Content-Disposition": f'inline; filename="{file_name}"'},
        )
    except OSError as exc:
        raise Http404("Image file is missing.") from exc

