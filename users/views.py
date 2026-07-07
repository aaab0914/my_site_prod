# Merged from package modules into a single file for simpler navigation.

# --- users/views/auth.py ---
from django.contrib import messages
from django.contrib.auth import login, logout
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import redirect, render

from .forms import UserLoginForm, UserRegisterForm

LOGIN_RATE_LIMIT_WINDOW = 900
LOGIN_RATE_LIMIT_MAX_FAILURES = 5


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
    return render(request, "users/register.html", {"form": form})


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
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return render(request, "users/logout.html")

# --- users/views/account.py ---
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from blog.models import Comment, Post

from .forms import UsernameChangeForm, UserProfileForm
from .models import Profile


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
        user_posts = Post.objects.filter(author=user).order_by("-publish")
        user_comments = Comment.objects.filter(author=user).order_by("-created")
    else:
        user_posts = Post.published.filter(author=user).order_by("-publish")
        user_comments = Comment.objects.filter(author=user, active=True).order_by("-created")
    return render(request, "users/profile.html", {"user": user, "posts": user_posts, "comments": user_comments})


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
