# Merged from package modules into a single file for simpler navigation.

import mimetypes
from pathlib import Path

# --- users/views/auth.py ---
from django.contrib import messages
from django.contrib.auth import login, logout
from django.core.cache import cache
from django.core.paginator import Paginator
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import redirect, render

from .forms import UserLoginForm, UserRegisterForm
from my_site.site_views import render_public_cached_template

LOGIN_RATE_LIMIT_WINDOW = 900
LOGIN_RATE_LIMIT_MAX_FAILURES = 5
AUTH_HTML_CACHE_TTL = 60 * 60 * 24 * 30


def _login_rate_limit_key(request):
    username = request.POST.get("username", "").strip().lower() or "anonymous"
    ip = request.META.get("REMOTE_ADDR", "unknown")
    return f"login-failures:{ip}:{username}"


def register(request):
    if request.user.is_authenticated:
        return redirect("blog:all_posts_list")
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Register Successful!")
            return redirect("blog:all_posts_list")
    else:
        form = UserRegisterForm()
    return render_public_cached_template(request, "view:users_register", "users/register.html", {"form": form}, timeout=AUTH_HTML_CACHE_TTL)


def login_view(request):
    if request.user.is_authenticated:
        return redirect("blog:all_posts_list")
    if request.method == "POST":
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
            return redirect("blog:all_posts_list")
        cache.set(rate_limit_key, failure_count + 1, timeout=LOGIN_RATE_LIMIT_WINDOW)
    else:
        form = UserLoginForm()
    return render_public_cached_template(request, "view:users_login", "users/login.html", {"form": form}, timeout=AUTH_HTML_CACHE_TTL)


def logout_view(request):
    if request.method == "POST":
        logout(request)
        return render(request, "users/logout.html", {"logged_out": True})
    return render_public_cached_template(request, "view:users_logout", "users/logout.html", {"logged_out": False}, timeout=AUTH_HTML_CACHE_TTL)

# --- users/views/account.py ---
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import http_date, parse_http_date_safe, quote_etag

from blog.models import AudioPost, Comment, Post, VideoPost
from images.models import Album, AlbumImage, ImagePost
from my_site.media_helpers import filter_existing_media_instances, media_file_exists

from .forms import UsernameChangeForm, UserProfileForm
from .models import Profile


def _valid_gallery_images_for_user(user, limit=12):
    return filter_existing_media_instances(
        ImagePost.objects.filter(uploaded_by=user).order_by('-created'),
        'image',
        limit=limit,
    )


def _valid_albums_for_user(user, limit=12):
    valid_album_ids = []
    albums = Album.objects.filter(uploaded_by=user).prefetch_related('images').order_by('-created')
    for album in albums:
        if any(media_file_exists(album_image.image) for album_image in album.images.all()):
            valid_album_ids.append(album.id)
        if len(valid_album_ids) >= limit:
            break
    if not valid_album_ids:
        return []
    album_map = {album.id: album for album in albums if album.id in valid_album_ids}
    return [album_map[album_id] for album_id in valid_album_ids if album_id in album_map]


def _valid_audio_posts_for_user(user, limit=12):
    return filter_existing_media_instances(
        AudioPost.objects.filter(uploaded_by=user).order_by('-created'),
        'audio_file',
        limit=limit,
    )


def _valid_video_posts_for_user(user, limit=12):
    return filter_existing_media_instances(
        VideoPost.objects.filter(uploaded_by=user).order_by('-created'),
        'video_file',
        limit=limit,
    )


@login_required
def profile_edit(request):
    if not hasattr(request.user, "profile"):
        Profile.objects.create(user=request.user)
    profile = request.user.profile
    if request.method == "POST":
        if "avatar" in request.FILES and not profile.can_change_avatar():
            remaining = profile.get_avatar_change_remaining_days()
            messages.error(
                request,
                f"You can change your avatar only once every 3 days. Please wait {remaining} more days.",
            )
            return redirect("users:profile_edit")
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            if "avatar" in request.FILES:
                profile.last_avatar_change = timezone.now()
                form.save()
                messages.success(request, "Your profile picture has been updated.")
            else:
                form.save()
                messages.success(request, "Your profile picture has been updated.")
            return redirect("users:profile")
    else:
        form = UserProfileForm(instance=profile)
    remaining = profile.get_avatar_change_remaining_days()
    return render(request, "users/profile_edit.html", {"form": form, "remaining_days": remaining})


@login_required
def profile(request, username=None):
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = request.user
    viewing_own_profile = user == request.user
    if viewing_own_profile:
        user_posts_queryset = Post.objects.filter(author=user).order_by("-publish")
        user_comments = Comment.objects.filter(author=user).order_by("-created")
    else:
        user_posts_queryset = Post.published.filter(author=user).order_by("-publish")
        user_comments = Comment.objects.filter(author=user, active=True).order_by("-created")

    user_gallery_images = _valid_gallery_images_for_user(user)
    user_albums = _valid_albums_for_user(user)
    user_audio_posts = _valid_audio_posts_for_user(user)
    user_video_posts = _valid_video_posts_for_user(user)
    posts_paginator = Paginator(user_posts_queryset, 10)
    posts_page_obj = posts_paginator.get_page(request.GET.get("posts_page"))

    return render(request, "users/profile.html", {
        "profile_user": user,
        "posts": posts_page_obj.object_list,
        "posts_page_obj": posts_page_obj,
        "posts_total_count": user_posts_queryset.count(),
        "comments": user_comments,
        "gallery_images": user_gallery_images,
        "albums": user_albums,
        "audio_posts": user_audio_posts,
        "video_posts": user_video_posts,
    })


def profile_avatar(request, username):
    user = get_object_or_404(User, username=username)
    profile = getattr(user, "profile", None)
    if not profile or not profile.avatar:
        raise Http404("Avatar not found.")

    file_path = Path(profile.avatar.path)
    if not file_path.is_file():
        raise Http404("Avatar not found.")

    stat_result = file_path.stat()
    last_modified = stat_result.st_mtime
    etag = quote_etag(f"avatar-{user.pk}-{int(last_modified)}-{stat_result.st_size}")

    if_none_match = request.headers.get("If-None-Match")
    if if_none_match and if_none_match == etag:
        response = HttpResponse(status=304)
    else:
        if_modified_since = parse_http_date_safe(request.headers.get("If-Modified-Since", ""))
        if if_modified_since and int(last_modified) <= if_modified_since:
            response = HttpResponse(status=304)
        else:
            content_type, _ = mimetypes.guess_type(file_path.name)
            response = FileResponse(open(file_path, "rb"), content_type=content_type or "application/octet-stream")
            response["Content-Disposition"] = f'inline; filename="{file_path.name}"'

    response["Cache-Control"] = "public, max-age=604800"
    response["ETag"] = etag
    response["Last-Modified"] = http_date(last_modified)
    return response


@login_required
def account_delete(request):
    if request.method == "POST" and request.POST.get("confirm_delete"):
        username = request.user.username
        request.user.delete()
        messages.success(request, f'Account "{username}" has been permanently deleted.')
        return redirect("blog:all_posts_list")
    return render(request, "users/account_delete.html")


@login_required
def username_change(request):
    if request.method == "POST":
        form = UsernameChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            new_username = form.cleaned_data["username"]
            form.save()
            messages.success(request, f'User "{new_username}" has been changed.')
            return redirect("users:profile")
        for error in form.errors.get("username", []):
            messages.error(request, error)
    else:
        form = UsernameChangeForm(instance=request.user)
    return render(request, "users/username_change.html", {"form": form})
