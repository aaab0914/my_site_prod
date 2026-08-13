import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from images.models import ImagePost


class GalleryMediaCacheTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp(prefix="gallery-media-cache-")
        self.settings = override_settings(MEDIA_ROOT=self.media_root)
        self.settings.enable()
        self.user = User.objects.create_user(username="cache-user", password="secret123")

    def tearDown(self):
        self.settings.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def test_gallery_media_uses_long_lived_conditional_cache(self):
        image = ImagePost.objects.create(
            title="cached",
            image=SimpleUploadedFile("cached.png", b"cached-image", content_type="image/png"),
            uploaded_by=self.user,
        )
        media_url = reverse("blog:images:gallery_media", args=[image.id])

        response = self.client.get(media_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "public, max-age=7776000, immutable")
        self.assertIn("ETag", response)
        self.assertIn("Last-Modified", response)

        cached_response = self.client.get(media_url, HTTP_IF_NONE_MATCH=response["ETag"])

        self.assertEqual(cached_response.status_code, 304)
        self.assertEqual(cached_response["ETag"], response["ETag"])
