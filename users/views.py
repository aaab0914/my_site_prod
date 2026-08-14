from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from rest_framework.authtoken.models import Token

from blog.models import AudioPost, Comment, Post, VideoPost
from images.models import Album, ImagePost
from my_site.site_views import queue_operation_success

from .forms import (
    UsernameChangeForm,
    UserLoginForm,
    UserProfileForm,
    UserRegisterForm,
)
from .models import Profile

LOGIN_RATE_LIMIT_WINDOW = 900
LOGIN_RATE_LIMIT_MAX_FAILURES = 5
TOKEN_REGENERATE_COOLDOWN_SECONDS = 60

PYTHON_API_EXAMPLES = [
    {
        "title": 'List published posts',
        "description": 'Fetch the first page of published posts.',
        "dom_id": 'example-1',
        "code": 'import requests\nTOKEN = "your-token-here"\nheaders = {"Authorization": f"Token {TOKEN}"}\nr = requests.get("https://rgavanp.kdns.fr/blog/api/posts/", headers=headers)\nprint(r.status_code)\nprint(r.json())',
    },
    {
        "title": 'Get a single post',
        "description": 'Retrieve one post by its numeric id.',
        "dom_id": 'example-2',
        "code": 'import requests\nTOKEN = "your-token-here"\nheaders = {"Authorization": f"Token {TOKEN}"}\nr = requests.get("https://rgavanp.kdns.fr/blog/api/posts/1/", headers=headers)\nprint(r.status_code)\nprint(r.json()["title"])',
    },
    {
        "title": 'Create a post',
        "description": 'Publish a new post with tags.',
        "dom_id": 'example-3',
        "code": 'import requests\nTOKEN = "your-token-here"\nheaders = {"Authorization": f"Token {TOKEN}"}\npayload = {"title": "My new post", "body": "Hello **world**.", "tags": ["python", "django"]}\nr = requests.post("https://rgavanp.kdns.fr/blog/api/posts/", headers=headers, json=payload)\nprint(r.status_code)\nprint(r.json())',
    },
    {
        "title": 'Search posts',
        "description": 'Search posts by a keyword.',
        "dom_id": 'example-4',
        "code": 'import requests\nTOKEN = "your-token-here"\nheaders = {"Authorization": f"Token {TOKEN}"}\nr = requests.get("https://rgavanp.kdns.fr/blog/api/posts/?search=python", headers=headers)\nprint(r.status_code)\nprint(r.json())',
    },
    {
        "title": 'Filter posts by tag',
        "description": 'Filter posts using a tag name.',
        "dom_id": 'example-5',
        "code": 'import requests\nTOKEN = "your-token-here"\nheaders = {"Authorization": f"Token {TOKEN}"}\nr = requests.get("https://rgavanp.kdns.fr/blog/api/posts/?tags__name=django", headers=headers)\nprint(r.status_code)\nprint(r.json())',
    },
    {
        "title": 'List comments',
        "description": 'Fetch the first page of comments.',
        "dom_id": 'example-6',
        "code": 'import requests\nTOKEN = "your-token-here"\nheaders = {"Authorization": f"Token {TOKEN}"}\nr = requests.get("https://rgavanp.kdns.fr/blog/api/comments/", headers=headers)\nprint(r.status_code)\nprint(r.json())',
    },
    {
        "title": 'Add a comment',
        "description": 'Post a comment on a post.',
        "dom_id": 'example-7',
        "code": 'import requests\nTOKEN = "your-token-here"\nheaders = {"Authorization": f"Token {TOKEN}"}\npayload = {"post": 1, "body": "Great post!"}\nr = requests.post("https://rgavanp.kdns.fr/blog/api/comments/", headers=headers, json=payload)\nprint(r.status_code)\nprint(r.json())',
    },
    {
        "title": 'List tags',
        "description": 'Fetch all available tags.',
        "dom_id": 'example-8',
        "code": 'import requests\nTOKEN = "your-token-here"\nheaders = {"Authorization": f"Token {TOKEN}"}\nr = requests.get("https://rgavanp.kdns.fr/blog/api/tags/", headers=headers)\nprint(r.status_code)\nprint(r.json())',
    },
    {
        "title": 'Get a tag',
        "description": 'Retrieve one tag by its slug.',
        "dom_id": 'example-9',
        "code": 'import requests\nTOKEN = "your-token-here"\nheaders = {"Authorization": f"Token {TOKEN}"}\nr = requests.get("https://rgavanp.kdns.fr/blog/api/tags/python/", headers=headers)\nprint(r.status_code)\nprint(r.json())',
    },
    {
        "title": 'Paginate results',
        "description": 'Browse a specific page of results.',
        "dom_id": 'example-10',
        "code": 'import requests\nTOKEN = "your-token-here"\nheaders = {"Authorization": f"Token {TOKEN}"}\nr = requests.get("https://rgavanp.kdns.fr/blog/api/posts/?page=2", headers=headers)\nprint(r.status_code)\ndata = r.json()\nprint("count:", data.get("count"), "next:", data.get("next"))',
    },
]


def api_token_issue(request):
    if request.method != "POST":
        return HttpResponse("POST required", status=405)
    user = authenticate(
        request,
        username=request.POST.get("username", ""),
        password=request.POST.get("password", ""),
    )
    if user is None:
        return JsonResponse({"detail": "Invalid credentials."}, status=400)
    token, _created = Token.objects.get_or_create(user=user)
    return JsonResponse({"user_id": user.id, "username": user.username, "token": token.key})


def _is_post_request(request):
    return request.method == "POST"


def _login_rate_limit_key(request):
    username = request.POST.get("username", "").strip().lower() or "anonymous"
    ip = request.META.get("REMOTE_ADDR", "unknown")
    return f"login-failures:{ip}:{username}"


def _redirect_to_post_list():
    return redirect("blog:all_posts_list")


def register(request):
    if request.user.is_authenticated:
        return _redirect_to_post_list()
    form = UserRegisterForm(request.POST or None)
    if _is_post_request(request) and form.is_valid():
        user = form.save()
        login(request, user)
        return queue_operation_success(
            request,
            title="Registration Complete",
            message=f'Account "{user.username}" has been created successfully.',
            primary_label="Open Profile",
            primary_url=reverse_lazy("users:profile"),
            secondary_label="Back to Blog",
            secondary_url=reverse_lazy("blog:all_posts_list"),
        )
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return _redirect_to_post_list()
    if _is_post_request(request):
        rate_limit_key = _login_rate_limit_key(request)
        failure_count = cache.get(rate_limit_key, 0)
        if failure_count >= LOGIN_RATE_LIMIT_MAX_FAILURES:
            return HttpResponse(
                "Too many failed login attempts. Please wait 15 minutes and try again.",
                status=429,
            )
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            cache.delete(rate_limit_key)
            login(request, user)
            return _redirect_to_post_list()
        cache.set(rate_limit_key, failure_count + 1, timeout=LOGIN_RATE_LIMIT_WINDOW)
    else:
        form = UserLoginForm()
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    if _is_post_request(request):
        logout(request)
        return render(request, "users/logout.html", {"logged_out": True})
    return render(request, "users/logout.html", {"logged_out": False})


@login_required
def profile_edit(request):
    if not hasattr(request.user, "profile"):
        Profile.objects.create(user=request.user)
    profile = request.user.profile
    form = UserProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if _is_post_request(request):
        if "avatar" in request.FILES and not profile.can_change_avatar():
            remaining = profile.get_avatar_change_remaining_days()
            messages.error(
                request,
                f"You can change your avatar only once every 3 days. Please wait {remaining} more days.",
            )
            return redirect("users:profile_edit")
        if form.is_valid():
            if "avatar" in request.FILES:
                profile.last_avatar_change = timezone.now()
            form.save()
            return queue_operation_success(
                request,
                title="Profile Updated",
                message="Your profile has been updated successfully.",
                primary_label="Open Profile",
                primary_url=reverse_lazy("users:profile"),
                secondary_label="Edit Again",
                secondary_url=reverse_lazy("users:profile_edit"),
            )
    remaining = profile.get_avatar_change_remaining_days()
    return render(request, "users/profile_edit.html", {"form": form, "remaining_days": remaining})


@login_required
def profile(request, username=None):
    profile_user = get_object_or_404(User, username=username) if username else request.user
    viewing_own_profile = profile_user == request.user

    if viewing_own_profile:
        posts_queryset = Post.objects.filter(author=profile_user).order_by("-publish", "-id")
        comments_queryset = Comment.objects.filter(author=profile_user).order_by("-created", "-id")
    else:
        posts_queryset = Post.published.filter(author=profile_user).order_by("-publish", "-id")
        comments_queryset = Comment.objects.filter(author=profile_user, active=True).order_by("-created", "-id")

    posts_page_obj = Paginator(posts_queryset, 10).get_page(request.GET.get("posts_page"))
    gallery_images = ImagePost.objects.select_related("uploaded_by").filter(uploaded_by=profile_user).order_by("-created", "-id")[:10]
    albums = Album.objects.select_related("uploaded_by").prefetch_related("images").filter(uploaded_by=profile_user).order_by("-created", "-id")[:10]
    audio_posts = AudioPost.objects.select_related("uploaded_by").filter(uploaded_by=profile_user, active=True).order_by("-created", "-id")[:10]
    video_posts = VideoPost.objects.select_related("uploaded_by").filter(uploaded_by=profile_user).order_by("-created", "-id")[:10]
    gallery_images = [item for item in gallery_images if item.image and default_storage.exists(item.image.name)]
    albums = [album for album in albums if any(image.image and default_storage.exists(image.image.name) for image in album.images.all())]
    audio_posts = [item for item in audio_posts if item.audio_file and default_storage.exists(item.audio_file.name)]
    video_posts = [item for item in video_posts if item.video_file and default_storage.exists(item.video_file.name)]

    return render(
        request,
        "users/profile.html",
        {
            "profile_user": profile_user,
            "posts": posts_page_obj.object_list,
            "posts_page_obj": posts_page_obj,
            "posts_total_count": posts_queryset.count(),
            "comments": comments_queryset,
            "gallery_images": gallery_images,
            "albums": albums,
            "audio_posts": audio_posts,
            "video_posts": video_posts,
        },
    )


@login_required
def account_delete(request):
    if _is_post_request(request) and request.POST.get("confirm_delete"):
        username = request.user.username
        user = request.user
        logout(request)
        user.delete()
        return queue_operation_success(
            request,
            title="Account Deleted",
            message=f'Account "{username}" has been permanently deleted.',
            primary_label="Back to Blog",
            primary_url=reverse_lazy("blog:all_posts_list"),
            secondary_label="Register New Account",
            secondary_url=reverse_lazy("users:register"),
        )
    return render(request, "users/account_delete.html")


@login_required
def username_change(request):
    form = UsernameChangeForm(request.POST or None, instance=request.user)
    if _is_post_request(request):
        if form.is_valid():
            new_username = form.cleaned_data["username"]
            form.save()
            return queue_operation_success(
                request,
                title="Username Updated",
                message=f'Your username has been changed to "{new_username}" successfully.',
                primary_label="Open Profile",
                primary_url=reverse_lazy("users:profile"),
                secondary_label="Back to Blog",
                secondary_url=reverse_lazy("blog:all_posts_list"),
            )
        for error in form.errors.get("username", []):
            messages.error(request, error)
    return render(request, "users/username_change.html", {"form": form})


@login_required
def api_token_manage(request):
    token, _created = Token.objects.get_or_create(user=request.user)
    cooldown_key = f"api-token-regenerated:{request.user.pk}"
    cooldown_until = cache.get(cooldown_key)
    now = timezone.now().timestamp()
    can_regenerate_token = not cooldown_until or now >= float(cooldown_until)

    if _is_post_request(request) and request.POST.get("action") == "regenerate":
        if can_regenerate_token:
            token.delete()
            token = Token.objects.create(user=request.user)
            cache.set(cooldown_key, now + TOKEN_REGENERATE_COOLDOWN_SECONDS, timeout=TOKEN_REGENERATE_COOLDOWN_SECONDS)
            return queue_operation_success(
                request,
                title="API Token Regenerated",
                message="Your API token has been regenerated successfully.",
                primary_label="Open Token Page",
                primary_url=reverse_lazy("users:api_token_manage"),
                secondary_label="Back to Profile",
                secondary_url=reverse_lazy("users:profile"),
            )
        messages.error(request, "Please wait before regenerating your API token again.")
        return redirect("users:api_token_manage")

    cooldown_until = cache.get(cooldown_key)
    now = timezone.now().timestamp()
    can_regenerate_token = not cooldown_until or now >= float(cooldown_until)
    seconds_until_regenerate = max(0, int(float(cooldown_until) - now)) if cooldown_until else 0
    profile = getattr(request.user, "profile", None)
    return render(
        request,
        "users/api_token.html",
        {
            "token": token,
            "can_regenerate_token": can_regenerate_token,
            "seconds_until_regenerate": seconds_until_regenerate,
            "generated_now": False,
            "is_admin_token": request.user.is_staff or request.user.is_superuser,
            "token_regeneration_remaining_days": profile.get_token_regeneration_remaining_days() if profile else 0,
            "token_regeneration_cooldown_days": Profile.TOKEN_REGEN_COOLDOWN_DAYS,
            "python_examples": PYTHON_API_EXAMPLES,
        },
    )
