from io import BytesIO
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from blog.models import AudioPost


class AudioRouteTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp(prefix="audio-route-tests-")
        self.settings = override_settings(MEDIA_ROOT=self.media_root)
        self.settings.enable()
        cache.clear()
        AudioPost.objects.all().delete()
        self.client = Client()
        self.user = User.objects.create_user(
            username="routeuser",
            email="route@example.com",
            password="testpass123",
        )

    def tearDown(self):
        cache.clear()
        self.settings.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def make_audio_file(self, name="sample.mp3", content=b"ID3 sample audio bytes"):
        return SimpleUploadedFile(name, content, content_type="audio/mpeg")

    def create_audio_post(self, music_name="Sample Track", description="Sample audio description"):
        return AudioPost.objects.create(
            uploaded_by=self.user,
            audio_file=self.make_audio_file(),
            description=description,
            music_name=music_name,
        )

    def test_audio_list_route(self):
        self.create_audio_post()
        response = self.client.get(reverse("blog:audio_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "blog/audio/audio_list.html")
        self.assertContains(response, "Sample Track")



    def test_audio_list_includes_mobile_and_safari_friendly_player_markup(self):
        self.create_audio_post()
        response = self.client.get(reverse("blog:audio_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="audio-player-shell"')
        self.assertContains(response, 'playsinline')
        self.assertContains(response, 'webkit-playsinline')
        self.assertContains(response, 'preload="metadata"')
        self.assertContains(response, '@supports (-webkit-touch-callout: none)')

    def test_audio_upload_post_submission(self):
        self.client.login(username="routeuser", password="testpass123")
        audio_content = BytesIO(b"ID3")
        audio_content.name = "sample.mp3"
        response = self.client.post(
            reverse("blog:audio_upload"),
            {
                "music_name": "Uploaded Sample",
                "description": "Uploaded by integration test",
                "audio_file": audio_content,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(AudioPost.objects.filter(music_name="Uploaded Sample").exists())
        self.assertContains(response, "Uploaded Sample")

    def test_audio_upload_route_requires_login(self):
        response = self.client.post(
            reverse("blog:audio_upload"),
            {"music_name": "Denied Upload", "description": "Should redirect to login"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:login"), response.url)

    def test_audio_edit_route_requires_login(self):
        audio = self.create_audio_post()
        response = self.client.get(reverse("blog:audio_post_edit", kwargs={"pk": audio.pk}))
        self.assertEqual(response.status_code, 302)

    def test_audio_delete_route_requires_login(self):
        audio = self.create_audio_post()
        response = self.client.get(reverse("blog:audio_post_delete", kwargs={"pk": audio.pk}))
        self.assertEqual(response.status_code, 302)

    def test_audio_delete_get_only_shows_confirmation(self):
        self.client.login(username="routeuser", password="testpass123")
        audio = self.create_audio_post()
        response = self.client.get(reverse("blog:audio_post_delete", kwargs={"pk": audio.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(AudioPost.objects.filter(pk=audio.pk).exists())

    def test_audio_edit_rejects_non_owner(self):
        owner = User.objects.create_user(username="audioowner", password="testpass123")
        audio = AudioPost.objects.create(
            uploaded_by=owner,
            audio_file=SimpleUploadedFile("sample.mp3", b"ID3 sample audio bytes", content_type="audio/mpeg"),
            description="Owner audio",
            music_name="Owner Track",
        )
        self.client.login(username="routeuser", password="testpass123")
        response = self.client.post(
            reverse("blog:audio_post_edit", kwargs={"pk": audio.pk}),
            {
                "music_name": "Hacked Track",
                "description": "Changed by another user",
                "audio_file": SimpleUploadedFile("clip.mp3", b"ID3 sample audio bytes", content_type="audio/mpeg"),
            },
        )
        self.assertEqual(response.status_code, 403)
        audio.refresh_from_db()
        self.assertEqual(audio.music_name, "Owner Track")

    def test_audio_delete_rejects_non_owner(self):
        owner = User.objects.create_user(username="audioowner2", password="testpass123")
        audio = AudioPost.objects.create(
            uploaded_by=owner,
            audio_file=SimpleUploadedFile("sample.mp3", b"ID3 sample audio bytes", content_type="audio/mpeg"),
            description="Owner audio",
            music_name="Owner Track",
        )
        self.client.login(username="routeuser", password="testpass123")
        response = self.client.post(reverse("blog:audio_post_delete", kwargs={"pk": audio.pk}))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(AudioPost.objects.filter(pk=audio.pk).exists())



    def test_audio_proxy_supports_range_requests(self):
        self.client.login(username="routeuser", password="testpass123")
        audio = self.create_audio_post()
        response = self.client.get(
            reverse("blog:audio_file_proxy", kwargs={"pk": audio.pk}),
            HTTP_RANGE="bytes=0-3",
        )
        self.assertEqual(response.status_code, 206)
        self.assertEqual(response["Accept-Ranges"], "bytes")
        self.assertTrue(response["Content-Range"].startswith("bytes 0-3/"))

class AudioUploadValidationTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp(prefix="audio-upload-tests-")
        self.settings = override_settings(MEDIA_ROOT=self.media_root)
        self.settings.enable()
        cache.clear()
        AudioPost.objects.all().delete()
        self.client = Client()
        self.user = User.objects.create_user(
            username="uploaduser",
            email="upload@example.com",
            password="testpass123",
        )
        self.client.login(username="uploaduser", password="testpass123")

    def tearDown(self):
        cache.clear()
        self.settings.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def test_audio_upload_accepts_multipart_submission(self):
        audio_file = SimpleUploadedFile("clip.mp3", b"ID3 sample audio bytes", content_type="audio/mpeg")
        response = self.client.post(
            reverse("blog:audio_upload"),
            {
                "music_name": "Multipart Audio",
                "description": "Audio upload test",
                "audio_file": audio_file,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(AudioPost.objects.filter(music_name="Multipart Audio").exists())

    def test_audio_upload_rejects_disallowed_file_type(self):
        audio_file = SimpleUploadedFile("clip.txt", b"not audio", content_type="text/plain")
        response = self.client.post(
            reverse("blog:audio_upload"),
            {
                "music_name": "Bad Audio",
                "description": "Invalid upload",
                "audio_file": audio_file,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AudioPost.objects.filter(music_name="Bad Audio").exists())
        self.assertContains(response, "Audio upload must be an MP3, WAV, or OGG file.")
