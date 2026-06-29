# ========================================
# IMPORTS
# ========================================

from django.shortcuts import render, redirect, get_object_or_404
# render: Renders a template with context data
# redirect: Redirects to a different URL
# get_object_or_404: Returns an object or raises 404 if not found

from django.contrib.auth import login, authenticate, logout
# login: Logs a user in (creates session)
# authenticate: Verifies user credentials
# logout: Logs a user out (clears session)

from django.contrib.auth.decorators import login_required
# login_required: Decorator that redirects to login page if user is not authenticated

from django.contrib import messages
# messages: Framework for sending one-time notifications to users

from django.contrib.auth.models import User
from django.core.cache import cache
from django.http import HttpResponse
# User: Built-in Django user model

from django.utils import timezone
# timezone: Timezone-aware datetime utilities

from django import forms
# forms: Django's form handling framework (for customizing form fields)

from .forms import (
    UserRegisterForm,  # Form for user registration
    UserLoginForm,  # Form for user login
    UserProfileForm,  # Form for editing user profile
    UsernameChangeForm,
)

from blog.models import Post, Comment

# Post: Blog post model
# Comment: Blog comment model


# ========================================
# VIEW: REGISTER
# ========================================

def register(request):
    """
    Handles user registration.

    GET request: Displays an empty registration form.
    POST request: Validates and saves the new user, then logs them in.

    Args:
        request: HTTP request object

    Returns:
        HTTP response: Registration page or redirect to blog home
    """
    if request.user.is_authenticated:
        return redirect('blog:all_posts_list')

    if request.method == 'POST':
        # User submitted registration data
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            # Form validation passed - create the user
            user = form.save()
            # Log the new user in immediately
            login(request, user)
            messages.success(request, 'Register Successful!')
            return redirect('blog:all_posts_list')
    else:
        # First visit to the page - show empty form
        form = UserRegisterForm()

    return render(
        request,
        'users/register.html',
        {'form': form}
    )


# ========================================
# VIEW: LOGIN
# ========================================

LOGIN_RATE_LIMIT_WINDOW = 900
LOGIN_RATE_LIMIT_MAX_FAILURES = 5


def _login_rate_limit_key(request):
    username = request.POST.get("username", "").strip().lower() or "anonymous"
    ip = request.META.get("REMOTE_ADDR", "unknown")
    return f"login-failures:{ip}:{username}"

def login_view(request):
    """
    Handles user login.

    GET request: Displays login form.
    POST request: Validates credentials and logs user in.

    Args:
        request: HTTP request object

    Returns:
        HTTP response: Login page or redirect to blog home
    """
    if request.user.is_authenticated:
        return redirect('blog:all_posts_list')

    if request.method == 'POST':
        rate_limit_key = _login_rate_limit_key(request)
        failure_count = cache.get(rate_limit_key, 0)
        if failure_count >= LOGIN_RATE_LIMIT_MAX_FAILURES:
            return HttpResponse(
                "Too many failed login attempts. Please wait 15 minutes and try again.",
                status=429,
            )

        # User submitted login credentials
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            # Credentials are valid - get the authenticated user
            user = form.get_user()
            cache.delete(rate_limit_key)
            login(request, user)
            return redirect('blog:all_posts_list')
        cache.set(rate_limit_key, failure_count + 1, timeout=LOGIN_RATE_LIMIT_WINDOW)
    else:
        # First visit to the page - show empty form
        form = UserLoginForm()

    return render(
        request,
        'users/login.html',
        {'form': form}
    )


# ========================================
# VIEW: PROFILE EDIT
# ========================================

@login_required
def profile_edit(request):
    """
    Handles editing user profile information.

    Ensures a Profile object exists for the user, then handles form submission
    for updating bio, location, birth_date, and avatar.

    Avatar change is restricted to once every 3 days.

    Args:
        request: HTTP request object

    Returns:
        HTTP response: Profile edit page
    """
    # Ensure the user has a Profile object
    # This is needed for users who registered before the Profile model was created
    if not hasattr(request.user, 'profile'):
        from .models import Profile
        Profile.objects.create(user=request.user)

    profile = request.user.profile

    if request.method == 'POST':
        # Check if user is trying to change avatar
        if 'avatar' in request.FILES:
            if not profile.can_change_avatar():
                # Avatar change is restricted (3-day cooldown)
                remaining = profile.get_avatar_change_remaining_days()
                messages.error(
                    request,
                    f'You can change your avatar only once every 3 days. '
                    f'Please wait {remaining} more days.'
                )
                return redirect('users:profile_edit')

        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            if 'avatar' in request.FILES:
                # Update last_avatar_change timestamp when avatar is changed
                profile.last_avatar_change = timezone.now()
                form.save()
                messages.success(request, 'Your profile picture has been updated.')
            else:
                # Update other profile fields without changing avatar
                form.save()
                messages.success(request, 'Your profile picture has been updated.')
            return redirect('users:profile')
    else:
        form = UserProfileForm(instance=profile)

    remaining = profile.get_avatar_change_remaining_days()

    return render(
        request,
        'users/profile_edit.html',
        {
            'form': form,
            'remaining_days': remaining,
        }
    )


# ========================================
# VIEW: LOGOUT
# ========================================

def logout_view(request):
    """
    Handles user logout.

    Args:
        request: HTTP request object

    Returns:
        HTTP response: Logout confirmation page
    """
    logout(request)
    return render(request, 'users/logout.html')


# ========================================
# VIEW: PROFILE (VIEW PROFILE)
# ========================================

@login_required
def profile(request, username=None):
    """
    Displays a user's profile page with their posts and comments.

    If username is provided, shows that user's profile.
    If no username is provided, shows the logged-in user's profile.

    Args:
        request: HTTP request object
        username: Optional username string

    Returns:
        HTTP response: Profile page
    """
    if username:
        # Show profile of a specific user
        user = get_object_or_404(User, username=username)
    else:
        # Show profile of the currently logged-in user
        user = request.user

    viewing_own_profile = user == request.user

    if viewing_own_profile:
        user_posts = Post.objects.filter(author=user).order_by('-publish')
        user_comments = Comment.objects.filter(author=user).order_by('-created')
    else:
        user_posts = Post.published.filter(author=user).order_by('-publish')
        user_comments = Comment.objects.filter(author=user, active=True).order_by('-created')

    return render(
        request,
        'users/profile.html',
        {
            'user': user,
            'posts': user_posts,
            'comments': user_comments
        }
    )


# ========================================
# VIEW: ACCOUNT DELETE
# ========================================

@login_required
def account_delete(request):
    """
    Handles permanent account deletion.

    POST request with 'confirm_delete' = True deletes the user account.
    GET request displays a confirmation page.

    Args:
        request: HTTP request object

    Returns:
        HTTP response: Account deletion confirmation page
    """
    if request.method == 'POST':
        if request.POST.get('confirm_delete'):
            # User confirmed deletion
            username = request.user.username
            request.user.delete()
            messages.success(
                request,
                f'Account "{username}" has been permanently deleted.'
            )
            return redirect('blog:all_posts_list')

    # Show confirmation page (GET request)
    return render(request, 'users/account_delete.html')


# ========================================
# VIEW: USERNAME CHANGE
# ========================================

@login_required
def username_change(request):
    """
    Handles username change for the logged-in user.

    Validates that the new username is not already taken,
    then updates the user's username.

    Args:
        request: HTTP request object

    Returns:
        HTTP response: Username change page
    """
    if request.method == 'POST':
        form = UsernameChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            new_username = form.cleaned_data['username']
            form.save()
            messages.success(
                request,
                f'User "{new_username}" has been changed.'
            )
            return redirect('users:profile')
        for error in form.errors.get('username', []):
            messages.error(request, error)
    else:
        form = UsernameChangeForm(instance=request.user)

    return render(request, 'users/username_change.html', {'form': form})
