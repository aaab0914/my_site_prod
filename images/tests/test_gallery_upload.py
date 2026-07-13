import base64
import shutil
import tempfile
from io import BytesIO
from pathlib import Path

from PIL import Image
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from images.forms import GallerySingleUploadForm
from images.admin import ImageAdmin
from images.models import Album, AlbumImage, ImagePost
from blog.models import Post
from images.sync import sync_gallery_media
from my_site.media_sync import maybe_sync_site_media


def make_test_image(name="test.png", image_format="PNG", color=(255, 0, 0)):
    buffer = BytesIO()
    image = Image.new("RGB", (32, 32), color)
    image.save(buffer, format=image_format)
    return SimpleUploadedFile(
        name,
        buffer.getvalue(),
        content_type=f"image/{image_format.lower()}",
    )


class GalleryUploadTests(TestCase):
    def setUp(self):
        cache.clear()
        self.media_root = tempfile.mkdtemp(prefix="gallery-upload-tests-")
        self.settings = override_settings(
            MEDIA_ROOT=self.media_root,
            MEDIA_SYNC_INTERVAL_SECONDS=0,
            MEDIA_SYNC_ENABLED=False,
        )
        self.settings.enable()
        self.user = User.objects.create_user(username="tester", password="secret123")
        self.other_user = User.objects.create_user(username="other", password="secret123")
        self.superuser = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="secret123",
        )
        self.client.force_login(self.user)

    def tearDown(self):
        cache.clear()
        self.settings.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def test_form_accepts_pasted_image_data_only(self):
        upload = make_test_image()
        data_url = "data:image/png;base64," + base64.b64encode(upload.read()).decode("ascii")

        form = GallerySingleUploadForm(
            data={
                "description": "pasted",
                "pasted_images_data": f'[{{"name":"clip.png","data_url":"{data_url}"}}]',
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(len(form.cleaned_data["images"]), 1)

    def test_view_accepts_local_file_upload(self):
        response = self.client.post(
            reverse("blog:images:gallery_upload"),
            data={
                "description": "local file",
                "images": make_test_image(name="local.png"),
                "pasted_images_data": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ImagePost.objects.count(), 1)

    def test_view_accepts_pasted_image_data_only(self):
        upload = make_test_image()
        data_url = "data:image/png;base64," + base64.b64encode(upload.read()).decode("ascii")

        response = self.client.post(
            reverse("blog:images:gallery_upload"),
            data={
                "description": "pasted file",
                "pasted_images_data": f'[{{"name":"clip.png","data_url":"{data_url}"}}]',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ImagePost.objects.count(), 1)


    def test_post_create_with_cover_image_creates_matching_gallery_image(self):
        response = self.client.post(
            reverse("blog:post_create"),
            data={
                "title": "Post With Cover",
                "body": "Body for cover image sync",
                "tags": "cover-sync",
                "cover_image": make_test_image(name="post-cover.png"),
            },
        )

        self.assertEqual(response.status_code, 302)
        post = Post.objects.get(title="Post With Cover")
        self.assertTrue(post.cover_image)
        self.assertTrue(
            ImagePost.objects.filter(
                image=post.cover_image.name,
                uploaded_by=self.user,
            ).exists(),
            "Publishing a post with a cover image should add the same file to gallery.",
        )

    def test_gallery_detail_loads(self):
        image = ImagePost.objects.create(
            title="detail",
            image=make_test_image(name="detail.png"),
            uploaded_by=self.user,
        )

        response = self.client.get(reverse("blog:images:gallery_detail", args=[image.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, image.title)

    def test_gallery_list_paginates_twenty_items_per_page(self):
        for index in range(21):
            ImagePost.objects.create(
                title=f"image-{index}",
                image=make_test_image(name=f"page-{index}.png"),
                uploaded_by=self.user,
            )

        with override_settings(MEDIA_SYNC_ENABLED=True):
            response = self.client.get(reverse("blog:images:gallery_list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["images"]), 20)
        self.assertTrue(response.context["page_obj"].has_next())

    def test_gallery_list_second_page_contains_remaining_items(self):
        for index in range(21):
            ImagePost.objects.create(
                title=f"image-{index}",
                image=make_test_image(name=f"page-two-{index}.png"),
                uploaded_by=self.user,
            )

        response = self.client.get(reverse("blog:images:gallery_list"), {"page": 2})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["images"]), 1)
        self.assertEqual(response.context["page_obj"].number, 2)

    def test_owner_can_delete_image(self):
        image = ImagePost.objects.create(
            title="owner-delete",
            image=make_test_image(name="owner-delete.png"),
            uploaded_by=self.user,
        )

        response = self.client.post(reverse("blog:images:gallery_delete", args=[image.id]))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(ImagePost.objects.filter(id=image.id).exists())

    def test_owner_can_edit_image_details(self):
        image = ImagePost.objects.create(
            title="before-edit",
            description="before",
            image=make_test_image(name="before-edit.png"),
            uploaded_by=self.user,
        )

        response = self.client.post(
            reverse("blog:images:gallery_edit", args=[image.id]),
            data={"title": "after-edit", "description": "after"},
        )

        self.assertEqual(response.status_code, 302)
        image.refresh_from_db()
        self.assertEqual(image.title, "after-edit")
        self.assertEqual(image.description, "after")

        detail_response = self.client.get(reverse("blog:images:gallery_detail", args=[image.id]))
        self.assertContains(detail_response, "after-edit")
        self.assertContains(detail_response, "after")

    def test_non_owner_cannot_delete_image(self):
        image = ImagePost.objects.create(
            title="blocked-delete",
            image=make_test_image(name="blocked-delete.png"),
            uploaded_by=self.user,
        )
        self.client.force_login(self.other_user)

        response = self.client.post(reverse("blog:images:gallery_delete", args=[image.id]))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(ImagePost.objects.filter(id=image.id).exists())

    def test_non_owner_cannot_edit_image_details(self):
        image = ImagePost.objects.create(
            title="blocked-edit",
            description="blocked",
            image=make_test_image(name="blocked-edit.png"),
            uploaded_by=self.user,
        )
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse("blog:images:gallery_edit", args=[image.id]),
            data={"title": "changed", "description": "changed"},
        )

        self.assertEqual(response.status_code, 302)
        image.refresh_from_db()
        self.assertEqual(image.title, "blocked-edit")
        self.assertEqual(image.description, "blocked")

    def test_superuser_can_delete_image(self):
        image = ImagePost.objects.create(
            title="admin-delete",
            image=make_test_image(name="admin-delete.png"),
            uploaded_by=self.user,
        )
        self.client.force_login(self.superuser)

        response = self.client.post(reverse("blog:images:gallery_delete", args=[image.id]))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(ImagePost.objects.filter(id=image.id).exists())

    def test_superuser_can_edit_image_details(self):
        image = ImagePost.objects.create(
            title="admin-edit",
            description="before",
            image=make_test_image(name="admin-edit.png"),
            uploaded_by=self.user,
        )
        self.client.force_login(self.superuser)

        response = self.client.post(
            reverse("blog:images:gallery_edit", args=[image.id]),
            data={"title": "admin-after", "description": "after"},
        )

        self.assertEqual(response.status_code, 302)
        image.refresh_from_db()
        self.assertEqual(image.title, "admin-after")
        self.assertEqual(image.description, "after")


    def test_gallery_edit_can_change_display_title_without_replacing_file(self):
        image = ImagePost.objects.create(
            title="old-gallery-title",
            description="before",
            image=make_test_image(name="rename-gallery.png"),
            uploaded_by=self.user,
        )

        response = self.client.post(
            reverse("blog:images:gallery_edit", args=[image.id]),
            data={"title": "new-gallery-title", "description": "before"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        image.refresh_from_db()
        self.assertEqual(image.title, "new-gallery-title")
        self.assertIn("rename-gallery", image.image.name)

    def test_owner_can_edit_album_title_and_description(self):
        album = Album.objects.create(title="Old Album", description="before", uploaded_by=self.user)
        AlbumImage.objects.create(
            album=album,
            title="cover",
            description="cover",
            image=make_test_image(name="album-cover.png"),
            uploaded_by=self.user,
        )

        response = self.client.post(
            reverse("blog:images:album_edit", args=[album.id]),
            data={"title": "New Album", "description": "after"},
        )

        self.assertEqual(response.status_code, 302)
        album.refresh_from_db()
        self.assertEqual(album.title, "New Album")
        self.assertEqual(album.description, "after")

    def test_non_owner_cannot_edit_album_title(self):
        album = Album.objects.create(title="Blocked Album", description="before", uploaded_by=self.user)
        AlbumImage.objects.create(
            album=album,
            title="cover",
            description="cover",
            image=make_test_image(name="blocked-album-cover.png"),
            uploaded_by=self.user,
        )
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse("blog:images:album_edit", args=[album.id]),
            data={"title": "Hacked Album", "description": "changed"},
        )

        self.assertEqual(response.status_code, 302)
        album.refresh_from_db()
        self.assertEqual(album.title, "Blocked Album")
        self.assertEqual(album.description, "before")

    def test_superuser_can_edit_album_title(self):
        album = Album.objects.create(title="Admin Album", description="before", uploaded_by=self.user)
        AlbumImage.objects.create(
            album=album,
            title="cover",
            description="cover",
            image=make_test_image(name="admin-album-cover.png"),
            uploaded_by=self.user,
        )
        self.client.force_login(self.superuser)

        response = self.client.post(
            reverse("blog:images:album_edit", args=[album.id]),
            data={"title": "Admin Album Updated", "description": "after"},
        )

        self.assertEqual(response.status_code, 302)
        album.refresh_from_db()
        self.assertEqual(album.title, "Admin Album Updated")
        self.assertEqual(album.description, "after")

    def test_image_model_is_registered_in_admin(self):
        self.assertIn(ImagePost, admin.site._registry)
        self.assertIsInstance(admin.site._registry[ImagePost], ImageAdmin)

    def test_form_accepts_pasted_image_data_when_base64_has_spaces(self):
        upload = make_test_image()
        data_url = "data:image/png;base64," + base64.b64encode(upload.read()).decode("ascii")
        broken_data_url = data_url.replace("+", " ")

        form = GallerySingleUploadForm(
            data={
                "description": "pasted",
                "pasted_images_data": f'[{{"name":"clip.png","data_url":"{broken_data_url}"}}]',
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(len(form.cleaned_data["images"]), 1)


    def test_sync_returns_no_gallery_changes_for_existing_post_cover_images_when_disabled(self):
        post = Post.objects.create(
            title="Existing Cover",
            slug="existing-cover",
            author=self.user,
            body="Body",
            status=Post.Status.PUBLISHED,
            cover_image=make_test_image(name="existing-cover.png"),
        )
        ImagePost.objects.filter(image=post.cover_image.name).delete()

        with override_settings(MEDIA_SYNC_ENABLED=False):
            result = sync_gallery_media()

        self.assertEqual(result["created_records"], 0)
        self.assertFalse(
            ImagePost.objects.filter(image=post.cover_image.name, uploaded_by=self.user).exists()
        )

    def test_sync_keeps_database_records_for_missing_files_when_disabled(self):
        image = ImagePost.objects.create(
            title="missing-file",
            image=make_test_image(name="missing-file.png"),
            uploaded_by=self.user,
        )
        file_name = image.image.name
        (Path(self.media_root) / file_name).unlink()

        with override_settings(MEDIA_SYNC_ENABLED=False):
            result = sync_gallery_media()

        self.assertEqual(result["deleted_records"], 0)
        self.assertTrue(ImagePost.objects.filter(id=image.id).exists())
        self.assertFalse(any(item["from"] == file_name for item in result["trashed_files"]))

    def test_sync_keeps_orphan_files_from_media_posts_when_disabled(self):
        orphan_dir = Path(self.media_root) / "posts" / "2026" / "07" / "07"
        orphan_dir.mkdir(parents=True, exist_ok=True)
        orphan_file = orphan_dir / "orphan.jpg"
        orphan_file.write_bytes(b"orphan")

        with override_settings(MEDIA_SYNC_ENABLED=False):
            result = sync_gallery_media()

        self.assertEqual(result["trashed_files"], [])
        self.assertTrue(orphan_file.exists())
        self.assertTrue(orphan_dir.exists())

    def test_model_delete_moves_media_file_to_trash(self):
        image = ImagePost.objects.create(
            title="delete-file",
            image=make_test_image(name="delete-file.png"),
            uploaded_by=self.user,
        )
        file_path = Path(self.media_root) / image.image.name
        trash_root = Path(self.media_root) / ".trash"

        self.assertTrue(file_path.exists())
        image.delete()

        self.assertFalse(file_path.exists())

    def test_gallery_list_sync_does_not_mutate_files_when_disabled(self):
        stale_image = ImagePost.objects.create(
            title="stale",
            image=make_test_image(name="stale.png"),
            uploaded_by=self.user,
        )
        (Path(self.media_root) / stale_image.image.name).unlink()

        orphan_dir = Path(self.media_root) / "posts" / "2026" / "07" / "07"
        orphan_dir.mkdir(parents=True, exist_ok=True)
        orphan_file = orphan_dir / "stray.jpg"
        orphan_file.write_bytes(b"stray")

        with override_settings(MEDIA_SYNC_ENABLED=False):
            maybe_sync_site_media()
            response = self.client.get(reverse("blog:images:gallery_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(ImagePost.objects.filter(id=stale_image.id).exists())
        self.assertTrue(orphan_file.exists())
