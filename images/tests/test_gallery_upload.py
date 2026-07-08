import base64
import shutil
import tempfile
from io import BytesIO
from pathlib import Path

from PIL import Image
from django.contrib import admin
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from images.forms import GalleryUploadForm
from images.admin import ImageAdmin
from images.models import ImagePost
from blog.models import Post
from images.sync import sync_gallery_media


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
        self.media_root = tempfile.mkdtemp(prefix="gallery-upload-tests-")
        self.settings = override_settings(
            MEDIA_ROOT=self.media_root,
            MEDIA_SYNC_INTERVAL_SECONDS=0,
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
        self.settings.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def test_form_accepts_pasted_image_data_only(self):
        upload = make_test_image()
        data_url = "data:image/png;base64," + base64.b64encode(upload.read()).decode("ascii")

        form = GalleryUploadForm(
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

    def test_image_model_is_registered_in_admin(self):
        self.assertIn(ImagePost, admin.site._registry)
        self.assertIsInstance(admin.site._registry[ImagePost], ImageAdmin)

    def test_form_accepts_pasted_image_data_when_base64_has_spaces(self):
        upload = make_test_image()
        data_url = "data:image/png;base64," + base64.b64encode(upload.read()).decode("ascii")
        broken_data_url = data_url.replace("+", " ")

        form = GalleryUploadForm(
            data={
                "description": "pasted",
                "pasted_images_data": f'[{{"name":"clip.png","data_url":"{broken_data_url}"}}]',
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(len(form.cleaned_data["images"]), 1)

    def test_sync_deletes_database_records_for_missing_files(self):
        image = ImagePost.objects.create(
            title="missing-file",
            image=make_test_image(name="missing-file.png"),
            uploaded_by=self.user,
        )
        file_name = image.image.name
        image.image.delete(save=False)

        result = sync_gallery_media()

        self.assertEqual(result["deleted_records"], 1)
        self.assertFalse(ImagePost.objects.filter(id=image.id).exists())
        self.assertFalse(any(item["from"] == file_name for item in result["trashed_files"]))

    def test_sync_deletes_orphan_files_from_media_posts(self):
        orphan_dir = Path(self.media_root) / "posts" / "2026" / "07" / "07"
        orphan_dir.mkdir(parents=True, exist_ok=True)
        orphan_file = orphan_dir / "orphan.jpg"
        orphan_file.write_bytes(b"orphan")

        result = sync_gallery_media()

        self.assertTrue(
            any(item["from"] == "posts/2026/07/07/orphan.jpg" for item in result["trashed_files"])
        )
        self.assertFalse(orphan_file.exists())
        self.assertFalse(orphan_dir.exists())
        self.assertTrue(any(Path(self.media_root, item["to"]).exists() for item in result["trashed_files"]))

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
        self.assertTrue(any(path.is_file() for path in trash_root.rglob("delete-file*.png")))

    def test_gallery_list_sync_removes_missing_records_and_orphan_files(self):
        stale_image = ImagePost.objects.create(
            title="stale",
            image=make_test_image(name="stale.png"),
            uploaded_by=self.user,
        )
        stale_image.image.delete(save=False)

        orphan_dir = Path(self.media_root) / "posts" / "2026" / "07" / "07"
        orphan_dir.mkdir(parents=True, exist_ok=True)
        orphan_file = orphan_dir / "stray.jpg"
        orphan_file.write_bytes(b"stray")

        response = self.client.get(reverse("blog:images:gallery_list"))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(ImagePost.objects.filter(id=stale_image.id).exists())
        self.assertFalse(orphan_file.exists())
        self.assertTrue(any(path.is_file() for path in (Path(self.media_root) / ".trash").rglob("stray.jpg")))
