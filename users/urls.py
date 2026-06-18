from django.urls import (
    path,
    include
)

from . import views

app_name = 'users'

urlpatterns = [
    path(
        'register/',
        views.register,
        name='register'
    ),
    path(
        'login/',
        views.login_view,
        name='login'
    ),
    path(
        'logout/',
        views.logout_view,
        name='logout'
    ),
    path(
        'profile_edit/',
        views.profile_edit,
        name='profile_edit'
    ),
    path('profile/', views.profile, name='profile'),
    path('account/delete/', views.account_delete, name='account_delete'),
    path('username/change/', views.username_change, name='username_change'),
    path('profile/<str:username>/', views.profile, name='profile_by_username'),
]