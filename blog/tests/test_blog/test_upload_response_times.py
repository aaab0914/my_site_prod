import shutil
import tempfile
import time
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from blog.models import AudioPost, VideoPost
from images.models import ImagePost


class UploadResponseTimeTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp(prefix="upload-response-time-tests-")
        self.override = override_settings(MEDIA_ROOT=self.media_root)
        self.override.enable()
        self.client = Client()
        self.user = User.objects.create_user(username="uploadtimer", password="testpass123")
        self.superuser = User.objects.create_superuser(
            username="uploadtimeradmin",
            email="uploadtimeradmin@example.com",
            password="testpass123",
        )

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    @staticmethod
    def image_upload():
        buffer = BytesIO()
        Image.new("RGB", (32, 32), color="navy").save(buffer, format="JPEG")
        return SimpleUploadedFile("timed-image.jpg", buffer.getvalue(), content_type="image/jpeg")

    def test_simulated_image_audio_and_video_upload_response_times(self):
        self.client.force_login(self.user)
        started = time.perf_counter()
        image_response = self.client.post(
            reverse("blog:images:gallery_upload"),
            {"description": "timed image", "images": self.image_upload(), "pasted_images_data": ""},
        )
        image_seconds = time.perf_counter() - started
        self.assertEqual(image_response.status_code, 302)
        self.assertEqual(ImagePost.objects.count(), 1)

        started = time.perf_counter()
        audio_response = self.client.post(
            reverse("blog:audio_upload"),
            {
                "music_name": "Timed Audio",
                "description": "timed audio",
                "audio_file": SimpleUploadedFile("timed-audio.mp3", b"ID3 timed audio", content_type="audio/mpeg"),
            },
        )
        audio_seconds = time.perf_counter() - started
        self.assertEqual(audio_response.status_code, 302)
        self.assertEqual(AudioPost.objects.count(), 1)

        self.client.force_login(self.superuser)
        started = time.perf_counter()
        video_response = self.client.post(
            reverse("blog:video_upload"),
            {
                "title": "Timed Video",
                "description": "timed video",
                "video_file": SimpleUploadedFile("timed-video.mp4", b"not-a-real-video", content_type="video/mp4"),
            },
        )
        video_seconds = time.perf_counter() - started
        self.assertEqual(video_response.status_code, 302)
        self.assertEqual(VideoPost.objects.count(), 1)

        print(f"SIMULATED_UPLOAD_TIMES image={image_seconds:.3f}s audio={audio_seconds:.3f}s video={video_seconds:.3f}s")
