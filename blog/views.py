from django.contrib import messages

from django.contrib.auth.decorators import login_required

from django.contrib.auth.mixins import LoginRequiredMixin

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, TrigramSimilarity

from django.core.exceptions import PermissionDenied

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

from django.db.models import Count, Q

from django.shortcuts import get_object_or_404, redirect, render

from django.urls import reverse_lazy

from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_POST

from django.views.generic.edit import DeleteView, UpdateView

from taggit.models import Tag

from .forms import (
    CommentForm,
    EmailPostForm,
    PostCreateForm,
    SearchForm,
    AudioUploadForm,
)

from .models import Post, Comment, AudioPost

def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    if request.method == "POST":
        form = EmailPostForm(request.POST)
        if form.is_valid():
            form.cleaned_data
    else:
        form = EmailPostForm()
    return render(request, "blog/post/share.html", {"post": post, "form": form})

@cache_page(120)
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
        return redirect(post.get_absolute_url())
    return render(request, "blog/post/create_post.html", {"form": form})

def post_delete_success(request):
    return render(request, "blog/post/post_delete_success.html")

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
        messages.success(request, "Comment deleted successfully.")
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
    else:
        form = AudioUploadForm()

    if request.method == "POST" and form.is_valid():
        audio = form.save(commit=False)
        audio.uploaded_by = request.user
        audio.save()
        messages.success(request, "Success upload audio")
        return redirect("blog:audio_list")

    return render(request, "blog/audio/upload_audio.html", {"form": form})

def audio_list(request):
    audios = AudioPost.objects.all().order_by("-created")
    return render(request, "blog/audio/audio_list.html", {"audios": audios})

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
    success_url = reverse_lazy("blog:audio_post_delete_success")
    context_object_name = "audiopost"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        obj = self.get_object()

        if obj.uploaded_by != request.user and not request.user.is_superuser:
            raise PermissionDenied("You are not allowed to delete this audio post.")

        return super().dispatch(request, *args, **kwargs)
