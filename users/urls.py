# Merged from package modules into a single file for simpler navigation.

# --- users/urls/auth.py ---
from django.urls import path

from . import views

auth_urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
]

# --- users/urls/profile.py ---
from django.urls import path

from . import views

profile_urlpatterns = [
    path("profile_edit/", views.profile_edit, name="profile_edit"),
    path("profile/", views.profile, name="profile"),
    path("profile/<str:username>/", views.profile, name="profile_by_username"),
]

# --- users/urls/account.py ---
from django.urls import path

from . import views

account_urlpatterns = [
    path("account/delete/", views.account_delete, name="account_delete"),
    path("username/change/", views.username_change, name="username_change"),
]

# --- users/urls/routes.py ---
app_name = "users"
urlpatterns = [*auth_urlpatterns, *profile_urlpatterns, *account_urlpatterns]
