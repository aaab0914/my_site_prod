from django.urls import include, path

from . import api_views, views
from .feeds import LatestPostsFeed, UserPostsFeed
from .views import AudioPostDeleteView, AudioPostEditView, PostDeleteView, PostEditView

app_name = "blog"

post_urlpatterns = [
    path("<int:year>/<int:month>/<int:day>/<slug:post_slug>/", views.post_detail, name="post_detail"),
    path("tag/<slug:tag_slug>/", views.post_list, name="post_list_by_tag"),
    path("", views.post_list, name="all_posts_list"),
    path("feed/", LatestPostsFeed(), name="post_feed"),
    path("feed/<str:username>/", UserPostsFeed(), name="user_feed"),
    path("search/", views.post_search, name="post_search"),
    path("create/", views.post_create, name="post_create"),
    path("media/post-cover/<int:pk>/", views.post_cover_image, name="post_cover_image"),
    path("<int:pk>/edit/", PostEditView.as_view(), name="post_edit"),
    path("<int:pk>/delete/", PostDeleteView.as_view(), name="post_delete"),
    path("post_delete_success/", views.post_delete_success, name="post_delete_success"),
]

comment_urlpatterns = [
    path("media/comment-image/<int:comment_id>/", views.comment_image, name="comment_image"),
    path("<int:post_id>/comment/", views.add_comment, name="post_comment"),
    path("<slug:post_slug>/<int:comment_id>/edit/", views.edit_comment, name="edit_comment"),
    path("<slug:post_slug>/<int:comment_id>/delete/", views.comment_delete, name="comment_delete"),
]

audio_urlpatterns = [
    path("media/audio/<int:pk>/", views.audio_file_proxy, name="audio_file_proxy"),
    path("media/audio-cover/<int:pk>/", views.audio_cover_image_proxy, name="audio_cover_image_proxy"),
    path("media/video/<int:pk>/", views.video_file_proxy, name="video_file_proxy"),
    path("audio/upload/", views.audio_upload, name="audio_upload"),
    path("audio/list/", views.audio_list, name="audio_list"),
    path("video/upload/", views.video_upload, name="video_upload"),
    path("video/list/", views.video_list, name="video_list"),
    path("audio/edit/<int:pk>/", AudioPostEditView.as_view(), name="audio_post_edit"),
    path("audio/delete/<int:pk>/", AudioPostDeleteView.as_view(), name="audio_post_delete"),
    path("audio/delete/success/", views.audio_post_delete_success, name="audio_post_delete_success"),
]

api_urlpatterns = [
    path("api/posts/", api_views.PostListAPIView.as_view(), name="api_post_list"),
    path("api/posts/<int:pk>/", api_views.PostDetailAPIView.as_view(), name="api_post_detail"),
    path("api/comments/", api_views.CommentListAPIView.as_view(), name="api_comment_list"),
    path("api/comments/<int:pk>/", api_views.CommentDetailAPIView.as_view(), name="api_comment_detail"),
    path("api/tags/", api_views.tag_list_api, name="api_tag_list"),
    path("api/tags/<slug:slug>/", api_views.tag_detail_api, name="api_tag_detail"),
]

urlpatterns = [
    *post_urlpatterns,
    path("users/", include("users.urls")),
    path("", include(("images.urls", "images"), namespace="images")),
    *comment_urlpatterns,
    *api_urlpatterns,
    *audio_urlpatterns,
]
