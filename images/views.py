from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.shortcuts import get_object_or_404, redirect, render

from .forms import GalleryImageEditForm, GalleryUploadForm
from .models import ImagePost
from my_site.media_sync import maybe_sync_site_media


def gallery_list(request):
    maybe_sync_site_media()
    images = [
        image
        for image in ImagePost.objects.select_related("uploaded_by").order_by("-created")
        if image.image and default_storage.exists(image.image.name)
    ]
    paginator = Paginator(images, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "images/gallery_list.html",
        {"images": page_obj.object_list, "page_obj": page_obj},
    )


def gallery_detail(request, image_id):
    maybe_sync_site_media()
    image = get_object_or_404(ImagePost.objects.select_related("uploaded_by"), pk=image_id)
    if not image.image or not default_storage.exists(image.image.name):
        messages.error(request, "Image file is missing.")
        return redirect("blog:images:gallery_list")

    can_manage = request.user.is_authenticated and (
        image.uploaded_by_id == request.user.id or request.user.is_superuser
    )
    return render(
        request,
        "images/gallery_detail.html",
        {"image": image, "can_manage": can_manage},
    )


@login_required
def gallery_upload(request):
    if request.method == "POST":
        form = GalleryUploadForm(request.POST, request.FILES)
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

            messages.success(request, f"Uploaded {created_count} image(s) to Gallery.")
            return redirect("blog:images:gallery_list")
        except ValidationError as exc:
            form.add_error("images", exc)
    else:
        form = GalleryUploadForm()

    return render(request, "images/gallery_upload.html", {"form": form})


@login_required
def gallery_delete(request, image_id):
    image = get_object_or_404(ImagePost, pk=image_id)
    if image.uploaded_by_id != request.user.id and not request.user.is_superuser:
        messages.error(request, "You do not have permission to delete this image.")
        return redirect("blog:images:gallery_detail", image_id=image.id)

    if request.method == "POST":
        image.delete()
        messages.success(request, "Image deleted.")
        return redirect("blog:images:gallery_list")

    return render(request, "images/gallery_delete_confirm.html", {"image": image})


@login_required
def gallery_edit(request, image_id):
    image = get_object_or_404(ImagePost, pk=image_id)
    if image.uploaded_by_id != request.user.id and not request.user.is_superuser:
        messages.error(request, "You do not have permission to edit this image.")
        return redirect("blog:images:gallery_detail", image_id=image.id)

    if request.method == "POST":
        form = GalleryImageEditForm(request.POST, instance=image)
        if form.is_valid():
            form.save()
            messages.success(request, "Image details updated.")
            return redirect("blog:images:gallery_detail", image_id=image.id)
    else:
        form = GalleryImageEditForm(instance=image)

    return render(request, "images/gallery_edit.html", {"form": form, "image": image})
