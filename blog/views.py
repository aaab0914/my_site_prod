import mimetypes
from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic.edit import DeleteView, UpdateView
from taggit.models import Tag

from .forms import (
    CommentForm,
    EmailPostForm,
    PostCreateForm,
    SearchForm,
    AudioUploadForm,
    VideoUploadForm,
)

from images.models import ImagePost
from .models import Post, Comment, AudioPost, VideoPost
from my_site.site_views import queue_operation_success


def _is_post_request(request):
    return request.method == "POST"


def _serve_uploaded_file(field_file):
    if not field_file:
        raise Http404("File not found.")

    file_path = Path(field_file.path)
    if not file_path.is_file():
        raise Http404("File not found.")

    content_type, _ = mimetypes.guess_type(file_path.name)
    response = FileResponse(open(file_path, "rb"), content_type=content_type or "application/octet-stream")
    response["Content-Disposition"] = f'inline; filename="{file_path.name}"'
    return response


def _redirect_to_comment_post(comment):
    return redirect(
        "blog:post_detail",
        year=comment.post.publish.year,
        month=comment.post.publish.month,
        day=comment.post.publish.day,
        post_slug=comment.post.slug,
    )



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


def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    if _is_post_request(request):
        form = EmailPostForm(request.POST)
        if form.is_valid():
            form.cleaned_data
    else:
        form = EmailPostForm()
    return render(request, "blog/post/share.html", {"post": post, "form": form})

def post_list(request, tag_slug=None):
    sort = request.GET.get("sort", "newest")
    sort_map = {
        "newest": ["-publish", "-id"],
        "oldest": ["publish", "id"],
        "title_asc": ["title", "id"],
        "title_desc": ["-title", "-id"],
        "updated": ["-updated", "-id"],
        "author": ["author__username", "title", "id"],
    }
    current_sort = sort if sort in sort_map else "newest"

    post_queryset = Post.published.select_related("author").prefetch_related("tags").order_by(*sort_map[current_sort])
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

    return render(
        request,
        "blog/post/all_posts_list.html",
        {
            "posts": posts,
            "tag": tag,
            "current_sort": current_sort,
            "sort_options": _build_sort_options(current_sort),
            "pagination_suffix": f"?sort={current_sort}",
        },
    )

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
    return render(
        request,
        "blog/post/post_detail.html",
        {
            "post": post,
            "comments": comments,
            "form": form,
            "similar_posts": similar_posts,
        },
    )

def post_search(request):
    form = SearchForm(request.GET or None)
    query = None
    raw_results = Post.published.none()
    results = []
    selected_sort = request.GET.get("sort", "relevance")
    sort_options = []
    total_results = 0
    page_obj = None

    if "query" in request.GET and form.is_valid():
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
        raw_results = (full_text_results | trigram_results).distinct().annotate(
            final_rank=SearchRank(search_vector, search_query) + (TrigramSimilarity("title", query) * 2)
        )

        sort_map = {
            "relevance": ["-final_rank", "-publish", "-id"],
            "newest": ["-publish", "-id"],
            "oldest": ["publish", "id"],
            "title_asc": ["title", "id"],
            "title_desc": ["-title", "-id"],
        }
        selected_sort = selected_sort if selected_sort in sort_map else "relevance"
        raw_results = raw_results.order_by(*sort_map[selected_sort])
        total_results = raw_results.count()
        page_obj = Paginator(raw_results, 10).get_page(request.GET.get("page"))
        results = [
            {
                "url": post.get_absolute_url(),
                "title": post.title,
                "meta": f"Published {post.publish.strftime('%Y-%m-%d')} by {post.author.username}",
                "body_html": post.body,
                "kind": "post",
            }
            for post in page_obj.object_list
        ]
        sort_options = [
            {"label": "Relevance", "url": f"?query={query}&sort=relevance", "active": selected_sort == "relevance"},
            {"label": "Newest", "url": f"?query={query}&sort=newest", "active": selected_sort == "newest"},
            {"label": "Oldest", "url": f"?query={query}&sort=oldest", "active": selected_sort == "oldest"},
            {"label": "A-Z", "url": f"?query={query}&sort=title_asc", "active": selected_sort == "title_asc"},
            {"label": "Z-A", "url": f"?query={query}&sort=title_desc", "active": selected_sort == "title_desc"},
        ]

    return render(
        request,
        "blog/post/search_post.html",
        {
            "form": form,
            "query": query,
            "results": results,
            "total_results": total_results,
            "selected_sort": selected_sort,
            "sort_options": sort_options,
            "page_obj": page_obj,
        },
    )

@login_required
def post_create(request):
    form = PostCreateForm(request.POST or None, request.FILES or None)
    if _is_post_request(request) and form.is_valid():
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
        return queue_operation_success(
            request,
            title="Post Created",
            message=f'"{post.title}" has been published successfully.',
            primary_label="View Post",
            primary_url=post.get_absolute_url(),
            secondary_label="Create Another Post",
            secondary_url=reverse_lazy("blog:post_create"),
        )
    return render(request, "blog/post/create_post.html", {"form": form})

def post_cover_image(request, pk):
    post = get_object_or_404(Post, pk=pk)
    return _serve_uploaded_file(post.cover_image)


def comment_image(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    return _serve_uploaded_file(comment.image)


def audio_file_proxy(request, pk):
    audio = get_object_or_404(AudioPost, pk=pk)
    return _serve_uploaded_file(audio.audio_file)


def video_file_proxy(request, pk):
    video = get_object_or_404(VideoPost, pk=pk)
    return _serve_uploaded_file(video.video_file)


def post_delete_success(request):
    return render(request, "blog/post/post_delete_success.html")

def audio_post_delete_success(request):
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

    return queue_operation_success(
        request,
        title="Comment Added",
        message=f'Your comment on "{post.title}" has been posted successfully.',
        primary_label="View Post",
        primary_url=post.get_absolute_url(),
        secondary_label="Back to Blog",
        secondary_url=reverse_lazy("blog:all_posts_list"),
    )

@login_required
def edit_comment(request, post_slug, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.post.slug != post_slug:
        return redirect("blog:post_list")

    if comment.author_id != request.user.id and not request.user.is_superuser:
        return _redirect_to_comment_post(comment)

    form = CommentForm(request.POST or None, request.FILES or None, instance=comment)

    if _is_post_request(request) and form.is_valid():
        form.save()
        return queue_operation_success(
            request,
            title="Comment Updated",
            message=f'Your comment on "{comment.post.title}" has been updated successfully.',
            primary_label="View Post",
            primary_url=comment.post.get_absolute_url(),
            secondary_label="Back to Blog",
            secondary_url=reverse_lazy("blog:all_posts_list"),
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
        return redirect("blog:post_list")

    if comment.author_id != request.user.id and not request.user.is_superuser:
        messages.error(request, "You are not allowed to delete this comment.")
        return _redirect_to_comment_post(comment)

    if _is_post_request(request):
        post = comment.post
        comment_preview = (comment.body or "").strip()[:80] or "Comment"
        comment.delete()
        return queue_operation_success(
            request,
            title="Comment Deleted",
            message=f'"{comment_preview}" has been deleted successfully.',
            primary_label="View Post",
            primary_url=post.get_absolute_url(),
            secondary_label="Back to Blog",
            secondary_url=reverse_lazy("blog:all_posts_list"),
        )

    return render(request, "blog/comment/delete_comment.html", {"comment": comment})

@login_required
def audio_upload(request):
    form = AudioUploadForm(request.POST or None, request.FILES or None)
    if _is_post_request(request):
        uploaded_files = request.FILES.getlist("audio_file")

        if not uploaded_files:
            form.add_error("audio_file", "Please choose at least one audio file.")
        elif len(uploaded_files) > 10:
            form.add_error("audio_file", "You can upload at most 10 audio files at once.")
        elif form.is_valid():
            description = form.cleaned_data.get("description", "")
            track_title = form.cleaned_data.get("music_name", "").strip()

            for index, uploaded_file in enumerate(uploaded_files):
                music_name = track_title if index == 0 and len(uploaded_files) == 1 else ""
                AudioPost.objects.create(
                    music_name=music_name,
                    audio_file=uploaded_file,
                    description=description,
                    uploaded_by=request.user,
                )

            track_message = "1 audio file has been uploaded successfully." if len(uploaded_files) == 1 else f"{len(uploaded_files)} audio files have been uploaded successfully."
            return queue_operation_success(
                request,
                title="Audio Upload Complete",
                message=track_message,
                primary_label="Open Audio Library",
                primary_url=reverse_lazy("blog:audio_list"),
                secondary_label="Upload More Audio",
                secondary_url=reverse_lazy("blog:audio_upload"),
            )

    return render(request, "blog/audio/upload_audio.html", {"form": form})

@login_required
def video_upload(request):
    form = VideoUploadForm(request.POST or None, request.FILES or None)
    if not request.user.is_superuser:
        messages.error(request, "Only superusers can upload videos.")
        return redirect("blog:all_posts_list")

    if _is_post_request(request) and form.is_valid():
        video = form.save(commit=False)
        video.uploaded_by = request.user
        video.save()
        return queue_operation_success(
            request,
            title="Video Upload Complete",
            message=f'"{video.title or video.get_video_filename()}" has been uploaded successfully.',
            primary_label="Open Video Library",
            primary_url=reverse_lazy("blog:video_list"),
            secondary_label="Upload Another Video",
            secondary_url=reverse_lazy("blog:video_upload"),
        )

    return render(request, "blog/video/upload_video.html", {"form": form})


def video_list(request):
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
    videos_queryset = VideoPost.objects.select_related("uploaded_by").order_by(*sort_map[current_sort])
    page_obj = Paginator(videos_queryset, 10).get_page(request.GET.get("page"))
    return render(
        request,
        "blog/video/video_list.html",
        {
            "videos": page_obj.object_list,
            "page_obj": page_obj,
            "current_sort": current_sort,
            "sort_options": _build_sort_options(current_sort),
            "pagination_suffix": f"?sort={current_sort}",
        },
    )


def audio_list(request):
    sort = request.GET.get("sort", "newest")
    sort_map = {
        "newest": ["-created", "-id"],
        "oldest": ["created", "id"],
        "title_asc": ["music_name", "id"],
        "title_desc": ["-music_name", "-id"],
        "updated": ["-updated", "-id"],
        "author": ["uploaded_by__username", "music_name", "id"],
    }
    current_sort = sort if sort in sort_map else "newest"
    audios_queryset = AudioPost.objects.select_related("uploaded_by").order_by(*sort_map[current_sort])
    page_obj = Paginator(audios_queryset, 10).get_page(request.GET.get("page"))
    return render(
        request,
        "blog/audio/audio_list.html",
        {
            "audios": page_obj.object_list,
            "page_obj": page_obj,
            "current_sort": current_sort,
            "sort_options": _build_sort_options(current_sort),
            "pagination_suffix": f"?sort={current_sort}",
        },
    )

class PostEditView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostCreateForm
    template_name = "blog/post/post_edit.html"
    context_object_name = "post"
    pk_url_kwarg = "pk"

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author != request.user and not request.user.is_superuser:
            raise PermissionDenied("You are not allowed to edit this post.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        post = form.save(commit=False)
        post.author = self.get_object().author
        post.status = Post.Status.PUBLISHED
        post.save()
        form.save_m2m()
        return queue_operation_success(
            self.request,
            title="Post Updated",
            message=f'"{post.title}" has been updated successfully.',
            primary_label="View Post",
            primary_url=post.get_absolute_url(),
            secondary_label="Back to Posts",
            secondary_url=reverse_lazy("blog:all_posts_list"),
        )

class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = "blog/post/post_delete.html"
    context_object_name = "post"
    pk_url_kwarg = "pk"

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.author != request.user and not request.user.is_superuser:
            raise PermissionDenied("You are not allowed to delete this post.")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        post = self.get_object()
        post_title = post.title
        post.delete()
        return queue_operation_success(
            self.request,
            title="Post Deleted",
            message=f'"{post_title}" has been deleted successfully.',
            primary_label="Back to Posts",
            primary_url=reverse_lazy("blog:all_posts_list"),
            secondary_label="Create New Post",
            secondary_url=reverse_lazy("blog:post_create"),
        )

class AudioPostEditView(LoginRequiredMixin, UpdateView):
    model = AudioPost
    form_class = AudioUploadForm
    template_name = "blog/audio/audio_post_edit.html"
    context_object_name = "audiopost"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        obj = self.get_object()

        if obj.uploaded_by != request.user and not request.user.is_superuser:
            raise PermissionDenied("You are not allowed to edit this audio post.")

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy("blog:audio_list")

class AudioPostDeleteView(LoginRequiredMixin, DeleteView):
    model = AudioPost
    template_name = "blog/audio/audio_post_delete.html"
    context_object_name = "audiopost"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        obj = self.get_object()

        if obj.uploaded_by != request.user and not request.user.is_superuser:
            raise PermissionDenied("You are not allowed to delete this audio post.")

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        audio = self.get_object()
        audio_title = audio.music_name or audio.get_audio_filename()
        audio.delete()
        return queue_operation_success(
            self.request,
            title="Audio Deleted",
            message=f'"{audio_title}" has been deleted successfully.',
            primary_label="Open Audio Library",
            primary_url=reverse_lazy("blog:audio_list"),
            secondary_label="Upload Audio",
            secondary_url=reverse_lazy("blog:audio_upload"),
        )
