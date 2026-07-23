import base64
import binascii
import json
import mimetypes
import os
import re
from pathlib import Path

from django.contrib import messages


from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import FileResponse, Http404, HttpResponse, HttpResponseNotModified, StreamingHttpResponse

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

from django.db.models import Count, Q

from django.shortcuts import get_object_or_404, redirect, render
from django.template.response import TemplateResponse

from django.urls import reverse_lazy

from django.views.decorators.http import require_POST
from django.utils.http import http_date, parse_http_date_safe, quote_etag

from django.views.generic.edit import DeleteView, UpdateView

from taggit.models import Tag

from .forms import (
    CommentForm,
    EmailPostForm,
    PostCreateForm,
    PostEditForm,
    SearchForm,
    AudioUploadForm,
    AudioPostEditForm,
    VideoPostEditForm,
    VideoUploadForm,
)

from images.forms import GallerySingleUploadForm
from images.models import ImagePost
from my_site.media_cleanup import authorized_media_delete
from my_site.sorting import build_sort_context
from my_site.site_views import queue_operation_success, render_public_cached_template
from my_site.media_helpers import invalidate_cache_keys, invalidate_public_view_caches, prime_serialized_list_cache
from .models import Post, Comment, AudioPost, VideoPost


_RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")


_PUBLIC_LIST_CACHE_TTL = 60 * 60 * 24 * 30  # 30 days
_PUBLIC_HTML_CACHE_TTL = 60 * 60 * 24 * 30


def _public_page_cache_key(prefix, *parts):
    normalized = ":".join(str(part or "") for part in parts)
    return f"{prefix}:{normalized}"


def _render_public_cached_template(request, cache_key, template_name, context, timeout=_PUBLIC_HTML_CACHE_TTL):
    return render_public_cached_template(request, cache_key, template_name, context, timeout=timeout)


def _invalidate_blog_public_views():
    invalidate_public_view_caches(
        "view:site_index",
        "view:post_list:1:all",
        "view:post_search:empty",
        "view:audio_list:1",
        "view:video_list:1",
        "view:gallery_list:page:1",
        "view:album_list:page:1",
    )


def _ordered_posts_from_ids(post_ids):
    posts = list(Post.published.filter(id__in=post_ids).select_related("author").prefetch_related("tags"))
    order_map = {post_id: index for index, post_id in enumerate(post_ids)}
    posts.sort(key=lambda post: order_map.get(post.id, len(order_map)))
    return posts


def _cached_post_ids(tag_slug=None):
    cache_key = f"post_list:ids:tag:{tag_slug or 'all'}"
    cached_ids = cache.get(cache_key)
    if cached_ids is not None:
        return cached_ids

    queryset = Post.published.select_related("author").prefetch_related("tags")
    if tag_slug:
        queryset = queryset.filter(tags__slug=tag_slug)

    cached_ids = list(queryset.values_list("id", flat=True))
    cache.set(cache_key, cached_ids, _PUBLIC_LIST_CACHE_TTL)
    return cached_ids


def _sort_posts(posts, selected_sort):
    if selected_sort == "oldest":
        return sorted(posts, key=lambda post: (post.publish, post.id))
    if selected_sort == "title_az":
        return sorted(posts, key=lambda post: ((post.title or "").lower(), -post.id))
    if selected_sort == "title_za":
        return sorted(posts, key=lambda post: ((post.title or "").lower(), -post.id), reverse=True)
    return sorted(posts, key=lambda post: (post.publish, post.id), reverse=True)


def _sort_serialized_items(items, selected_sort, *, title_key, created_key):
    if selected_sort == "oldest":
        return sorted(items, key=lambda item: (item.get(created_key) or "", item.get("id") or 0))
    if selected_sort == "title_az":
        return sorted(items, key=lambda item: ((item.get(title_key) or "").lower(), -(item.get("id") or 0)))
    if selected_sort == "title_za":
        return sorted(items, key=lambda item: ((item.get(title_key) or "").lower(), -(item.get("id") or 0)), reverse=True)
    return sorted(items, key=lambda item: (item.get(created_key) or "", item.get("id") or 0), reverse=True)


def _cached_post_list_page(page_number, tag_slug=None):
    normalized_page = str(page_number or 1)
    cache_key = f"post_list:page:{normalized_page}:tag:{tag_slug or 'all'}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    queryset = Post.published.select_related("author").prefetch_related("tags")
    if tag_slug:
        queryset = queryset.filter(tags__slug=tag_slug)

    paginator = Paginator(queryset, 10)
    try:
        page_obj = paginator.page(normalized_page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    payload = {
        "post_ids": list(page_obj.object_list.values_list("id", flat=True)),
        "number": page_obj.number,
        "paginator_count": paginator.count,
        "num_pages": paginator.num_pages,
    }
    cache.set(cache_key, payload, _PUBLIC_LIST_CACHE_TTL)
    return payload


def _cached_search_result_ids(query):
    normalized_query = (query or "").strip()
    if not normalized_query:
        return []

    cache_key = f"post_search:query:{normalized_query.lower()}"
    cached_ids = cache.get(cache_key)
    if cached_ids is not None:
        return cached_ids

    search_vector = SearchVector("title", weight="A") + SearchVector("body", weight="B")
    search_query = SearchQuery(normalized_query)
    full_text_results = (
        Post.published.annotate(rank=SearchRank(search_vector, search_query))
        .filter(rank__gte=0.1)
        .order_by("-rank", "-publish")
    )

    trigram_results = (
        Post.published.annotate(
            title_similarity=TrigramSimilarity("title", normalized_query),
            body_similarity=TrigramSimilarity("body", normalized_query),
            total_similarity=(TrigramSimilarity("title", normalized_query) * 2 + TrigramSimilarity("body", normalized_query)),
        )
        .filter(Q(title_similarity__gt=0.1) | Q(body_similarity__gt=0.1))
        .order_by("-total_similarity", "-publish")
    )

    combined_results = (full_text_results | trigram_results).distinct()
    result_ids = list(
        combined_results.annotate(
            final_rank=SearchRank(search_vector, search_query) + (TrigramSimilarity("title", normalized_query) * 2)
        ).order_by("-final_rank", "-publish").values_list("id", flat=True)
    )
    cache.set(cache_key, result_ids, _PUBLIC_LIST_CACHE_TTL)
    return result_ids


def _range_stream(file_obj, start, end, chunk_size=8192):
    file_obj.seek(start)
    remaining = end - start + 1
    while remaining > 0:
        chunk = file_obj.read(min(chunk_size, remaining))
        if not chunk:
            break
        remaining -= len(chunk)
        yield chunk


def _serve_uploaded_file(field_file, request=None):
    if not field_file:
        raise Http404("File not found.")

    file_path = Path(field_file.path)
    if not file_path.is_file():
        raise Http404("File not found.")

    stat_result = os.stat(file_path)
    last_modified = stat_result.st_mtime
    file_size = stat_result.st_size
    etag = quote_etag(f"upload-{file_path.name}-{int(last_modified)}-{file_size}")

    if request is not None:
        if_none_match = request.headers.get("If-None-Match")
        if if_none_match and if_none_match == etag:
            response = HttpResponseNotModified()
        else:
            if_modified_since = parse_http_date_safe(request.headers.get("If-Modified-Since", ""))
            if if_modified_since and int(last_modified) <= if_modified_since:
                response = HttpResponseNotModified()
            else:
                response = None
    else:
        response = None

    content_type, _ = mimetypes.guess_type(file_path.name)
    content_type = content_type or "application/octet-stream"

    if response is None and request is not None:
        range_header = request.headers.get("Range", "").strip()
        match = _RANGE_RE.fullmatch(range_header)
        if match:
            start_raw, end_raw = match.groups()
            if start_raw == "" and end_raw == "":
                return HttpResponse(status=416)

            if start_raw == "":
                length = int(end_raw)
                start = max(file_size - length, 0)
                end = file_size - 1
            else:
                start = int(start_raw)
                end = int(end_raw) if end_raw else file_size - 1

            if start >= file_size or start < 0 or end < start:
                range_response = HttpResponse(status=416)
                range_response["Content-Range"] = f"bytes */{file_size}"
                range_response["Accept-Ranges"] = "bytes"
                return range_response

            end = min(end, file_size - 1)
            length = end - start + 1
            file_handle = open(file_path, "rb")
            response = StreamingHttpResponse(
                _range_stream(file_handle, start, end),
                status=206,
                content_type=content_type,
            )
            response["Content-Length"] = str(length)
            response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
            response["Content-Disposition"] = f'inline; filename="{file_path.name}"'
        else:
            response = None

    if response is None:
        response = FileResponse(open(file_path, "rb"), content_type=content_type)
        response["Content-Disposition"] = f'inline; filename="{file_path.name}"'
        response["Content-Length"] = str(file_size)

    response["Accept-Ranges"] = "bytes"
    response["Cache-Control"] = "public, max-age=604800"
    response["ETag"] = etag
    response["Last-Modified"] = http_date(last_modified)
    return response


def _redirect_non_superuser_home(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        response = redirect("blog:all_posts_list")
        response["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, private"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        response["Vary"] = "Cookie"
        return response
    return None



def _decode_pasted_image_uploads(raw_value):
    raw_value = (raw_value or "").strip()
    if not raw_value:
        return []
    try:
        items = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise ValidationError("Pasted image data is invalid.") from exc

    uploads = []
    for index, item in enumerate(items, start=1):
        data_url = item.get("data_url", "")
        if ";base64," not in data_url:
            raise ValidationError("Pasted image data is invalid.")
        header, encoded = data_url.split(";base64,", 1)
        mime_type = header.replace("data:", "", 1).strip().lower()
        if mime_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise ValidationError("Image must be a JPEG, PNG, or WebP file.")
        try:
            content = base64.b64decode(encoded.replace(" ", "+"))
        except (binascii.Error, ValueError) as exc:
            raise ValidationError("Pasted image data is invalid.") from exc
        extension = mime_type.split("/")[-1]
        uploads.append(SimpleUploadedFile(item.get("name") or f"pasted-image-{index}.{extension}", content, content_type=mime_type))
    return uploads


def _handle_post_edit_media_upload(request, post):
    uploaded_files = list(request.FILES.getlist("media_files"))
    try:
        pasted_uploads = _decode_pasted_image_uploads(request.POST.get("pasted_images_data", ""))
    except ValidationError as exc:
        return str(exc)

    all_uploads = uploaded_files + pasted_uploads
    if not all_uploads:
        return "Select at least one image or audio file."
    if len(all_uploads) > 10:
        return "A maximum of 10 files can be uploaded at one time."

    image_count = 0
    audio_count = 0
    for upload in all_uploads:
        lower_name = (upload.name or "").lower()
        content_type = getattr(upload, "content_type", "") or ""

        if lower_name.endswith((".jpg", ".jpeg", ".png", ".webp")) or content_type.startswith("image/"):
            image_form = GallerySingleUploadForm(files={"images": [upload]})
            image = upload
            try:
                from images.forms import optimize_uploaded_image
                image = optimize_uploaded_image(upload)
            except ValidationError as exc:
                return str(exc)
            image_post = ImagePost(
                title=(image.name.rsplit(".", 1)[0].strip() or f"post-image-{post.pk}"),
                description="",
                uploaded_by=request.user,
            )
            image_post.image = image
            image_post.save()
            image_count += 1
            continue

        if lower_name.endswith((".mp3", ".wav", ".ogg")) or content_type.startswith("audio/"):
            try:
                AudioUploadForm.validate_audio_upload(upload)
            except ValidationError as exc:
                return str(exc)
            audio_post = AudioPost(
                music_name="",
                audio_file=upload,
                description="",
                uploaded_by=request.user,
            )
            audio_post.save()
            audio_count += 1
            continue

        return "Only JPEG, PNG, WebP, MP3, WAV, and OGG files are supported."

    invalidate_cache_keys("audio_list:ids", "audio_list:items", "gallery_list:valid_image_ids")
    _invalidate_blog_public_views()
    total = image_count + audio_count
    messages.success(request, f"Uploaded {total} media file{'s' if total != 1 else ''} successfully.")
    return None


def _serialize_audio_item(audio):
    return {
        "id": audio.id,
        "music_name": audio.music_name,
        "description": audio.description,
        "uploaded_by_username": audio.uploaded_by.username,
        "created": audio.created.isoformat() if audio.created else "",
        "audio_url": audio.get_audio_proxy_url(),
        "cover_url": audio.get_cover_image_proxy_url(),
        "cover_filename": audio.get_cover_filename(),
    }


def _prime_audio_list_cache(new_items=None):
    return prime_serialized_list_cache(
        "audio_list:ids",
        "audio_list:items",
        AudioPost.objects.select_related("uploaded_by"),
        _serialize_audio_item,
        new_items=new_items,
    )


def _serialize_video_item(video):
    return {
        "id": video.id,
        "title": video.title,
        "description": video.description,
        "uploaded_by_username": video.uploaded_by.username,
        "created": video.created.isoformat() if video.created else "",
        "video_url": video.get_video_proxy_url(),
        "filename": video.get_video_filename(),
    }


def _prime_video_list_cache(new_items=None):
    return prime_serialized_list_cache(
        "video_list:ids",
        "video_list:items",
        VideoPost.objects.select_related("uploaded_by"),
        _serialize_video_item,
        new_items=new_items,
    )

def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    if request.method == "POST":
        form = EmailPostForm(request.POST)
        if form.is_valid():
            form.cleaned_data
    else:
        form = EmailPostForm()
    return render(request, "blog/post/share.html", {"post": post, "form": form})

def post_list(request, tag_slug=None):
    tag = get_object_or_404(Tag, slug=tag_slug) if tag_slug else None
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
    post_ids = _cached_post_ids(tag.slug if tag else None)
    posts = _sort_posts(_ordered_posts_from_ids(post_ids), sort_context["selected_sort"])
    page_obj = Paginator(posts, 10).get_page(request.GET.get("page"))

    context = {"posts": page_obj, "tag": tag, **sort_context}
    cache_key = _public_page_cache_key("view:post_list", request.GET.get("page", 1), tag.slug if tag else "all", sort_context["selected_sort"])
    return _render_public_cached_template(request, cache_key, "blog/post/all_posts_list.html", context)

def post_detail(request, year, month, day, post_slug):
    post = Post.published.filter(
        slug=post_slug,
        publish__year=year,
        publish__month=month,
        publish__day=day,
    ).order_by('-publish', '-id').first()
    if post is None:
        raise Http404("No Post matches the given query.")
    comments = post.comments.filter(active=True)
    form = CommentForm()
    post_tags_ids = post.tags.values_list("id", flat=True)

    similar_posts_cache_key = f"post_detail:similar_posts:{post.pk}"
    similar_post_ids = cache.get(similar_posts_cache_key)
    if similar_post_ids is None:
        tag_based_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)

        title_based_posts = Post.published.none()
        if tag_based_posts.count() < 4:
            title_based_posts = (
                Post.published.annotate(similarity=TrigramSimilarity("title", post.title))
                .filter(similarity__gt=0.1)
                .exclude(id=post.id)
                .order_by("-similarity")[: 4 - tag_based_posts.count()]
            )

        similar_posts = (tag_based_posts | title_based_posts).distinct()
        similar_posts = similar_posts.annotate(same_tags=Count("tags")).order_by("-same_tags", "-publish")[:4]
        similar_post_ids = list(similar_posts.values_list("id", flat=True))
        cache.set(similar_posts_cache_key, similar_post_ids, 600)
    similar_posts = list(Post.published.filter(id__in=similar_post_ids).select_related("author"))
    similar_posts.sort(key=lambda item: similar_post_ids.index(item.id))
    return render(
        request,
        "blog/post/post_detail.html",
        {
            "post": post,
            "comments": comments,
            "form": form,
            "similar_posts": similar_posts,
            "post_update_success": request.session.pop("post_update_success_once", False),
        },
    )

def post_search(request):
    form = SearchForm()
    query = None
    results = []
    if "query" in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data["query"]
            result_ids = _cached_search_result_ids(query)
            results = _ordered_posts_from_ids(result_ids)
    sort_context = build_sort_context(
        request,
        {
            "relevance": "Relevance",
            "newest": "Newest",
            "oldest": "Oldest",
            "title_az": "Title A-Z",
            "title_za": "Title Z-A",
        },
        default_sort="relevance",
    )
    if query and sort_context["selected_sort"] != "relevance":
        results = _sort_posts(results, sort_context["selected_sort"])
    context = {"form": form, "query": query, "results": results, "total_results": len(results), **sort_context}
    cache_suffix = (query or "").strip().lower() or "empty"
    cache_key = _public_page_cache_key("view:post_search", cache_suffix, sort_context["selected_sort"])
    return _render_public_cached_template(request, cache_key, "blog/post/search_post.html", context)

@login_required
def post_create(request):
    if request.method == "POST":
        form = PostCreateForm(request.POST, request.FILES)
    else:
        form = PostCreateForm()
    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.status = Post.Status.PUBLISHED
        post.save()
        form.save_m2m()
        if post.cover_image:
            ImagePost.objects.get_or_create(
                image=post.cover_image.name,
                defaults={
                    "title": post.title,
                    "description": "",
                    "uploaded_by": request.user,
                },
            )
            invalidate_cache_keys("gallery_list:valid_image_ids")
        _invalidate_blog_public_views()
        invalidate_cache_keys("post_list:page:1:tag:all")
        _invalidate_blog_public_views()
        for tag in post.tags.all():
            if tag.slug:
                invalidate_cache_keys(f"post_list:page:1:tag:{tag.slug}")
        return queue_operation_success(
            request,
            title="Post Published",
            message=f'Post "{post.title}" was published successfully.',
            primary_label="View New Post",
            primary_url=post.get_absolute_url(),
        )
    return render(request, "blog/post/create_post.html", {"form": form})


@login_required
def post_create_success(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author_id != request.user.id and not request.user.is_superuser:
        raise PermissionDenied("Permission denied for viewing this success page.")
    return queue_operation_success(
        request,
        title="Post Published",
        message=f'Post "{post.title}" was published successfully.',
        primary_label="View New Post",
        primary_url=post.get_absolute_url(),
    )


@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author_id != request.user.id and not request.user.is_superuser:
        raise PermissionDenied("Permission denied for editing this post.")

    form = PostEditForm(instance=post)

    if request.method == "POST" and request.POST.get("post_action") == "save_post":
        form = PostEditForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save()
            request.session["post_update_success_once"] = True
            return queue_operation_success(
                request,
                title="Post Updated",
                message=f'Post "{post.title}" was updated successfully.',
                primary_label="View Post",
                primary_url=post.get_absolute_url(),
            )

    return render(
        request,
        "blog/post/post_edit.html",
        {"form": form, "post": post},
    )

def post_cover_image(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return _serve_uploaded_file(post.cover_image, request=request)


def comment_image(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    return _serve_uploaded_file(comment.image, request=request)


def audio_file_proxy(request, pk):
    audio = get_object_or_404(AudioPost, pk=pk)
    return _serve_uploaded_file(audio.audio_file, request=request)


def audio_cover_image_proxy(request, pk):
    audio = get_object_or_404(AudioPost, pk=pk)
    return _serve_uploaded_file(audio.cover_image, request=request)




def video_upload(request):
    denied = _redirect_non_superuser_home(request)
    if denied:
        return denied

    if request.method == "POST":
        form = VideoUploadForm(request.POST, request.FILES)
        if form.is_valid():
            video_post = form.save(commit=False)
            video_post.uploaded_by = request.user
            video_post.save()
            _prime_video_list_cache([video_post])
            _invalidate_blog_public_views()
            messages.success(request, "Video uploaded successfully.")
            return queue_operation_success(
                request,
                title="Video Uploaded",
                message="Your video was uploaded successfully.",
                primary_label="Open Video List",
                primary_url=reverse_lazy("blog:video_list"),
            )
    else:
        form = VideoUploadForm()

    return render(request, "blog/video/upload_video.html", {"form": form})


def video_file_proxy(request, pk):
    video = get_object_or_404(VideoPost, pk=pk)
    return _serve_uploaded_file(video.video_file, request=request)

def post_delete_success(request):
    return redirect("operation_success")


def audio_post_delete_success(request):
    return redirect("operation_success")

@login_required
@require_POST
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comment = None
    form = CommentForm(request.POST, request.FILES)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.email = request.user.email or f"{request.user.username}@example.invalid"
        comment.save()

    return render(
        request,
        "blog/comment/add_comment_success.html",
        {"post": post, "form": form, "comment": comment},
    )

@login_required
def edit_comment(request, post_slug, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.post.slug != post_slug:
        comment = None
    if comment is None:
        return redirect("blog:post_list")

    if comment.author_id != request.user.id and not request.user.is_superuser:
        return redirect(
            "blog:post_detail",
            year=comment.post.publish.year,
            month=comment.post.publish.month,
            day=comment.post.publish.day,
            post_slug=comment.post.slug,
        )

    if request.method == "POST":
        form = CommentForm(request.POST, request.FILES, instance=comment)
    else:
        form = CommentForm(instance=comment)

    if request.method == "POST" and form.is_valid():
        form.save()
        return queue_operation_success(
            request,
            title="Comment Updated",
            message="Your comment was updated successfully.",
            primary_label="Back to Post",
            primary_url=reverse_lazy(
                "blog:post_detail",
                kwargs={
                    "year": comment.post.publish.year,
                    "month": comment.post.publish.month,
                    "day": comment.post.publish.day,
                    "post_slug": comment.post.slug,
                },
            ),
        )

    return render(
        request,
        "blog/comment/edit_comment.html",
        {"form": form, "comment": comment, "post": comment.post},
    )

@login_required
def comment_delete(request, post_slug, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.post.slug != post_slug:
        comment = None
    if comment is None:
        return redirect("blog:post_list")

    if comment.author_id != request.user.id and not request.user.is_superuser:
        messages.error(request, "Permission denied for deleting this comment.")
        return redirect(
            "blog:post_detail",
            year=comment.post.publish.year,
            month=comment.post.publish.month,
            day=comment.post.publish.day,
            post_slug=comment.post.slug,
        )

    if request.method == "POST":
        post = comment.post
        comment.delete()
        return queue_operation_success(
            request,
            title="Comment Deleted",
            message="Your comment was deleted successfully.",
            primary_label="Back to Post",
            primary_url=reverse_lazy(
                "blog:post_detail",
                kwargs={"year": post.publish.year, "month": post.publish.month, "day": post.publish.day, "post_slug": post.slug},
            ),
        )

    return render(request, "blog/comment/delete_comment.html", {"comment": comment})

@login_required
def audio_upload(request):
    if request.method == "POST":
        form = AudioUploadForm(request.POST, request.FILES)
        uploaded_files = request.FILES.getlist("audio_file")

        if not uploaded_files:
            form.add_error("audio_file", "Select at least one audio file.")
        elif len(uploaded_files) > 10:
            form.add_error("audio_file", "A maximum of 10 audio files can be uploaded at once.")
        elif form.is_valid():
            description = form.cleaned_data.get("description", "")
            track_title = form.cleaned_data.get("music_name", "").strip()
            cover_image = form.cleaned_data.get("cover_image")

            created_audio_posts = []
            for index, uploaded_file in enumerate(uploaded_files):
                music_name = track_title if index == 0 and len(uploaded_files) == 1 else ""
                audio_post = AudioPost(
                    music_name=music_name,
                    audio_file=uploaded_file,
                    description=description,
                    uploaded_by=request.user,
                )
                if cover_image and index == 0 and len(uploaded_files) == 1:
                    audio_post.cover_image = cover_image
                audio_post.save()
                created_audio_posts.append(audio_post)

            _prime_audio_list_cache(created_audio_posts)
            _invalidate_blog_public_views()
            if len(uploaded_files) == 1:
                messages.success(request, "Audio uploaded successfully.")
                message = "Audio uploaded successfully."
            else:
                messages.success(request, f"Uploaded {len(uploaded_files)} audio files successfully.")
                message = f"Uploaded {len(uploaded_files)} audio files successfully."
            return queue_operation_success(
                request,
                title="Audio Uploaded",
                message=message,
                primary_label="Open Audio List",
                primary_url=reverse_lazy("blog:audio_list"),
            )
    else:
        form = AudioUploadForm()

    return render(request, "blog/audio/upload_audio.html", {"form": form})

def video_detail(request, pk):
    denied = _redirect_non_superuser_home(request)
    if denied:
        return denied

    video = get_object_or_404(VideoPost.objects.select_related("uploaded_by"), pk=pk)
    return render(request, "blog/video/video_detail.html", {
        "video": video,
        "filename": video.get_video_filename(),
        "video_url": video.get_video_proxy_url(),
    })


def video_edit(request, pk):
    denied = _redirect_non_superuser_home(request)
    if denied:
        return denied

    videopost = get_object_or_404(VideoPost, pk=pk)
    if request.method == "POST":
        form = VideoPostEditForm(request.POST, request.FILES, instance=videopost)
        if form.is_valid():
            if not form.cleaned_data.get("video_file"):
                form.instance.video_file = videopost.video_file
            form.save()
            invalidate_cache_keys("video_list:ids", "video_list:items")
            _prime_video_list_cache([videopost])
            messages.success(request, "Video updated successfully.")
            return queue_operation_success(
                request,
                title="Video Updated",
                message="Video details were updated successfully.",
                primary_label="View Video",
                primary_url=reverse_lazy("blog:video_detail", kwargs={"pk": videopost.pk}),
            )
    else:
        form = VideoPostEditForm(instance=videopost)
    return render(request, "blog/video/video_edit.html", {"form": form, "videopost": videopost})


def video_delete(request, pk):
    denied = _redirect_non_superuser_home(request)
    if denied:
        return denied

    videopost = get_object_or_404(VideoPost, pk=pk)
    if request.method == "POST":
        videopost.delete()
        invalidate_cache_keys("video_list:ids", "video_list:items")
        messages.success(request, "Video deleted successfully.")
        return queue_operation_success(
            request,
            title="Video Deleted",
            message="The video was deleted successfully.",
            primary_label="Open Video List",
            primary_url=reverse_lazy("blog:video_list"),
        )
    return render(request, "blog/video/video_delete.html", {"videopost": videopost})


def video_list(request):
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
    video_items = cache.get("video_list:items")
    if video_items is None or (not video_items and VideoPost.objects.exists()):
        video_items = _prime_video_list_cache() or []
    video_items = _sort_serialized_items(video_items, sort_context["selected_sort"], title_key="title", created_key="created")
    paginator = Paginator(video_items, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    context = {"videos": page_obj.object_list, "page_obj": page_obj, **sort_context}
    cache_key = _public_page_cache_key("view:video_list", request.GET.get("page", 1), sort_context["selected_sort"])
    return _render_public_cached_template(request, cache_key, "blog/video/video_list.html", context)

def audio_list(request):
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
    audio_cache = cache.get("audio_list:items")
    if audio_cache is None or (not audio_cache and AudioPost.objects.exists()):
        audio_cache = _prime_audio_list_cache() or []
    audio_cache = _sort_serialized_items(audio_cache, sort_context["selected_sort"], title_key="music_name", created_key="created")
    paginator = Paginator(audio_cache, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    context = {"audios": page_obj.object_list, "page_obj": page_obj, **sort_context}
    cache_key = _public_page_cache_key("view:audio_list", request.GET.get("page", 1), sort_context["selected_sort"])
    return _render_public_cached_template(request, cache_key, "blog/audio/audio_list.html", context)

class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = "blog/post/post_delete.html"
    success_url = reverse_lazy("operation_success")
    context_object_name = "post"
    pk_url_kwarg = "pk"

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author != request.user and not request.user.is_superuser:
            raise PermissionDenied("Permission denied for deleting this post.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.request.session["operation_success"] = {
            "title": "Post Deleted",
            "message": "The selected post was deleted successfully.",
            "primary_label": "Back to Posts",
            "primary_url": str(reverse_lazy("blog:all_posts_list")),
            "secondary_label": "Create Post",
            "secondary_url": str(reverse_lazy("blog:post_create")),
        }
        return super().form_valid(form)

class AudioPostEditView(LoginRequiredMixin, UpdateView):
    model = AudioPost
    form_class = AudioPostEditForm
    template_name = "blog/audio/audio_post_edit.html"
    context_object_name = "audiopost"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        obj = self.get_object()

        if obj.uploaded_by != request.user and not request.user.is_superuser:
            raise PermissionDenied("Permission denied for editing this audio post.")

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy("operation_success")

    def form_valid(self, form):
        if self.request.POST.get("remove_cover_image") == "1" and self.object.cover_image:
            with authorized_media_delete():
                self.object.cover_image.delete(save=False)
            self.object.cover_image = None
            form.instance.cover_image = None
        response = super().form_valid(form)
        invalidate_cache_keys("audio_list:ids", "audio_list:items")
        _invalidate_blog_public_views()
        self.request.session["operation_success"] = {
            "title": "Audio Updated",
            "message": "Audio details were updated successfully.",
            "primary_label": "Open Audio List",
            "primary_url": str(reverse_lazy("blog:audio_list")),
            "secondary_label": "Blog Home",
            "secondary_url": str(reverse_lazy("blog:all_posts_list")),
        }
        return response

class AudioPostDeleteView(LoginRequiredMixin, DeleteView):
    model = AudioPost
    template_name = "blog/audio/audio_post_delete.html"
    success_url = reverse_lazy("operation_success")
    context_object_name = "audiopost"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        obj = self.get_object()

        if obj.uploaded_by != request.user and not request.user.is_superuser:
            raise PermissionDenied("Permission denied for deleting this audio post.")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.request.session["operation_success"] = {
            "title": "Audio Deleted",
            "message": "The selected audio track was deleted successfully.",
            "primary_label": "Back to Library",
            "primary_url": str(reverse_lazy("blog:audio_list")),
            "secondary_label": "Upload Audio",
            "secondary_url": str(reverse_lazy("blog:audio_upload")),
        }
        response = super().form_valid(form)
        invalidate_cache_keys("audio_list:ids", "audio_list:items")
        _invalidate_blog_public_views()
        return response
