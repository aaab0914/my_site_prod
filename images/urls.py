from django.urls import path

from . import views

app_name = "images"

urlpatterns = [
    path("gallery/", views.gallery_list, name="gallery_list"),
    path("gallery/upload/", views.gallery_upload, name="gallery_upload"),
    path("gallery/<int:image_id>/edit/", views.gallery_edit, name="gallery_edit"),
    path("gallery/<int:image_id>/delete/", views.gallery_delete, name="gallery_delete"),
    path("gallery/<int:image_id>/", views.gallery_detail, name="gallery_detail"),
]
