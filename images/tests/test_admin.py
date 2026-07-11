import shutil
import tempfile
from io import BytesIO

from PIL import Image
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from images.admin import AlbumAdmin, AlbumImageAdmin, AlbumImageInline, ImageAdmin
from images.models import Album, AlbumImage, ImagePost


def make_test_image(name="test.png", image_format="PNG", color=(255, 0, 0)):
    buffer = BytesIO()
    image = Image.new("RGB", (32, 32), color)
    image.save(buffer, format=image_format)
    return buffer.getvalue()


class ImageAdminTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp(prefix="image-admin-tests-")
        self.override = override_settings(MEDIA_ROOT=self.media_root)
        self.override.enable()
        self.user = User.objects.create_user(username="tester", password="secret123")
        self.superuser = User.objects.create_superuser(
            username="adminimg",
            email="adminimg@example.com",
            password="secret123",
        )
        self.client = Client()

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def test_image_admin_thumbnail_preview_renders_img(self):
        image = ImagePost.objects.create(
            title="Test Image",
            image=SimpleUploadedFile("test.png", make_test_image(), content_type="image/png"),
            uploaded_by=self.user,
        )
        model_admin = ImageAdmin(ImagePost, admin.site)
        self.assertIn("<img", model_admin.thumbnail_preview(image))

    def test_album_admin_cover_preview_renders_img(self):
        album = Album.objects.create(title="Album", description="desc", uploaded_by=self.user)
        AlbumImage.objects.create(
            album=album,
            title="Cover",
            image=SimpleUploadedFile("cover.png", make_test_image(), content_type="image/png"),
            uploaded_by=self.user,
        )
        model_admin = AlbumAdmin(Album, admin.site)
        self.assertIn("<img", model_admin.cover_preview(album))

    def test_album_image_admin_thumbnail_preview_renders_img(self):
        album = Album.objects.create(title="Album", description="desc", uploaded_by=self.user)
        image = AlbumImage.objects.create(
            album=album,
            title="Album Image",
            image=SimpleUploadedFile("album.png", make_test_image(), content_type="image/png"),
            uploaded_by=self.user,
        )
        model_admin = AlbumImageAdmin(AlbumImage, admin.site)
        self.assertIn("<img", model_admin.thumbnail_preview(image))

    def test_album_admin_uses_album_image_inline(self):
        model_admin = AlbumAdmin(Album, admin.site)
        self.assertIn(AlbumImageInline, model_admin.inlines)

    def test_image_admin_changelist_is_available_for_superuser(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin:images_imagepost_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Image posts")

    def test_image_admin_change_page_is_available_for_superuser(self):
        image = ImagePost.objects.create(
            title="Test Image",
            image=SimpleUploadedFile("test.png", make_test_image(), content_type="image/png"),
            uploaded_by=self.user,
        )
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin:images_imagepost_change", args=[image.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Image")

    def test_album_admin_change_page_is_available_for_superuser(self):
        album = Album.objects.create(title="Album", description="desc", uploaded_by=self.user)
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin:images_album_change", args=[album.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Album")
