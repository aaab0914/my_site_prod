from django.urls import path

from . import views

app_name = "images"

urlpatterns = [
    path("album/", views.album_list, name="album_list"),
    path("album/upload/", views.album_upload, name="album_upload"),
    path("album/<int:image_id>/edit/", views.album_edit, name="album_edit"),
    path("album/<int:image_id>/delete/", views.album_delete, name="album_delete"),
    path("album/<int:image_id>/media/", views.album_media, name="album_media"),
    path("album/<int:image_id>/", views.album_detail, name="album_detail"),
    path("gallery/", views.gallery_list, name="gallery_list"),
    path("gallery/upload/", views.gallery_upload, name="gallery_upload"),
    path("gallery/<int:image_id>/edit/", views.gallery_edit, name="gallery_edit"),
    path("gallery/<int:image_id>/delete/", views.gallery_delete, name="gallery_delete"),
    path("gallery/<int:image_id>/media/", views.gallery_media, name="gallery_media"),
    path("gallery/<int:image_id>/", views.gallery_detail, name="gallery_detail"),
]
