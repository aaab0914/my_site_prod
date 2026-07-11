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
from my_site.media_helpers import invalidate_cache_keys, prime_serialized_list_cache
from my_site.media_sync import maybe_sync_site_media
from .models import Post, Comment, AudioPost, VideoPost


_RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)")


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
        return "Please choose at least one image or audio file."
    if len(all_uploads) > 10:
        return "You can upload at most 10 files at one time."

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
    post_queryset = Post.published.select_related("author").prefetch_related("tags")
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_queryset = post_queryset.filter(tags__in=[tag])

    paginator = Paginator(post_queryset, 10)
    page_number = request.GET.get("page", 1)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)

    return render(request, "blog/post/all_posts_list.html", {"posts": posts, "tag": tag})

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

            search_vector = SearchVector("title", weight="A") + SearchVector("body", weight="B")
            search_query = SearchQuery(query)
            full_text_results = (
                Post.published.annotate(rank=SearchRank(search_vector, search_query))
                .filter(rank__gte=0.1)
                .order_by("-rank", "-publish")
            )

            trigram_results = (
                Post.published.annotate(
                    title_similarity=TrigramSimilarity("title", query),
                    body_similarity=TrigramSimilarity("body", query),
                    total_similarity=(TrigramSimilarity("title", query) * 2 + TrigramSimilarity("body", query)),
                )
                .filter(Q(title_similarity__gt=0.1) | Q(body_similarity__gt=0.1))
                .order_by("-total_similarity", "-publish")
            )

            combined_results = (full_text_results | trigram_results).distinct()
            results = combined_results.annotate(
                final_rank=SearchRank(search_vector, search_query) + (TrigramSimilarity("title", query) * 2)
            ).order_by("-final_rank", "-publish")
    return render(request, "blog/post/search_post.html", {"form": form, "query": query, "results": results})

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
        return redirect(post.get_absolute_url())
    return render(request, "blog/post/create_post.html", {"form": form})


@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author_id != request.user.id and not request.user.is_superuser:
        raise PermissionDenied("You are not allowed to edit this post.")

    form = PostEditForm(instance=post)

    if request.method == "POST" and request.POST.get("post_action") == "save_post":
        form = PostEditForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save()
            request.session["post_update_success_once"] = True
            return redirect(post.get_absolute_url())

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
            messages.success(request, "Video uploaded successfully.")
            return redirect("blog:video_list")
    else:
        form = VideoUploadForm()

    recent_videos = VideoPost.objects.select_related("uploaded_by").order_by("-created")[:12]
    return render(request, "blog/video/upload_video.html", {"form": form, "recent_videos": recent_videos})


def video_file_proxy(request, pk):
    denied = _redirect_non_superuser_home(request)
    if denied:
        return denied
    video = get_object_or_404(VideoPost, pk=pk)
    return _serve_uploaded_file(video.video_file, request=request)

def post_delete_success(request):
    if not request.session.pop("post_delete_success_once", False):
        return redirect("blog:all_posts_list")
    return render(request, "blog/post/post_delete_success.html")

def audio_post_delete_success(request):
    if not request.session.pop("audio_post_delete_success_once", False):
        return redirect("blog:audio_list")
    return render(request, "blog/audio/audio_post_delete_success.html")

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
        return redirect(
            "blog:post_detail",
            year=comment.post.publish.year,
            month=comment.post.publish.month,
            day=comment.post.publish.day,
            post_slug=comment.post.slug,
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
        messages.error(request, "You are not allowed to delete this comment.")
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
        return redirect(
            "blog:post_detail",
            year=post.publish.year,
            month=post.publish.month,
            day=post.publish.day,
            post_slug=post.slug,
        )

    return render(request, "blog/comment/delete_comment.html", {"comment": comment})

@login_required
def audio_upload(request):
    if request.method == "POST":
        form = AudioUploadForm(request.POST, request.FILES)
        uploaded_files = request.FILES.getlist("audio_file")

        if not uploaded_files:
            form.add_error("audio_file", "Please choose at least one audio file.")
        elif len(uploaded_files) > 10:
            form.add_error("audio_file", "You can upload at most 10 audio files at once.")
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
            if len(uploaded_files) == 1:
                messages.success(request, "Audio uploaded successfully.")
            else:
                messages.success(request, f"Uploaded {len(uploaded_files)} audio files successfully.")
            return redirect("blog:audio_list")
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
            messages.success(request, "Video updated successfully.")
            return redirect("blog:video_detail", pk=videopost.pk)
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
        messages.success(request, "Video deleted successfully.")
        return redirect("blog:video_list")
    return render(request, "blog/video/video_delete.html", {"videopost": videopost})


def video_list(request):
    video_items = cache.get("video_list:items")
    if video_items is None or (not video_items and VideoPost.objects.exists()):
        video_items = _prime_video_list_cache() or []
    paginator = Paginator(video_items, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "blog/video/video_list.html", {"videos": page_obj.object_list, "page_obj": page_obj})

def audio_list(request):
    maybe_sync_site_media()
    audio_cache = cache.get("audio_list:items")
    if audio_cache is None or (not audio_cache and AudioPost.objects.exists()):
        audio_cache = _prime_audio_list_cache() or []
    paginator = Paginator(audio_cache, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "blog/audio/audio_list.html", {"audios": page_obj.object_list, "page_obj": page_obj})

class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = "blog/post/post_delete.html"
    success_url = reverse_lazy("blog:post_delete_success")
    context_object_name = "post"
    pk_url_kwarg = "pk"

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author != request.user and not request.user.is_superuser:
            raise PermissionDenied("You are not allowed to delete this post.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.request.session["post_delete_success_once"] = True
        return super().form_valid(form)

class AudioPostEditView(LoginRequiredMixin, UpdateView):
    model = AudioPost
    form_class = AudioPostEditForm
    template_name = "blog/audio/audio_post_edit.html"
    context_object_name = "audiopost"

    def dispatch(self, request, *args, **kwargs):
        maybe_sync_site_media()
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        obj = self.get_object()

        if obj.uploaded_by != request.user and not request.user.is_superuser:
            raise PermissionDenied("You are not allowed to edit this audio post.")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        if self.request.POST.get("remove_cover_image") == "1" and self.object.cover_image:
            self.object.cover_image.delete(save=False)
            self.object.cover_image = None
            form.instance.cover_image = None
        response = super().form_valid(form)
        invalidate_cache_keys("audio_list:ids", "audio_list:items")
        return response

    def get_success_url(self):
        return reverse_lazy("blog:audio_list")

class AudioPostDeleteView(LoginRequiredMixin, DeleteView):
    model = AudioPost
    template_name = "blog/audio/audio_post_delete.html"
    success_url = reverse_lazy("blog:audio_post_delete_success")
    context_object_name = "audiopost"

    def dispatch(self, request, *args, **kwargs):
        maybe_sync_site_media()
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        obj = self.get_object()

        if obj.uploaded_by != request.user and not request.user.is_superuser:
            raise PermissionDenied("You are not allowed to delete this audio post.")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.request.session["audio_post_delete_success_once"] = True
        response = super().form_valid(form)
        invalidate_cache_keys("audio_list:ids", "audio_list:items")
        return response
