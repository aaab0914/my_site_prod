import shutil
import tempfile

from django.contrib import admin
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from blog.admin import AudioPostAdmin, VideoPostAdmin
from blog.models import AudioPost, VideoPost


@override_settings(ALLOWED_HOSTS=["testserver", "localhost"])
class AdminCustomTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp(prefix="admin-custom-tests-")
        self.override = override_settings(MEDIA_ROOT=self.media_root)
        self.override.enable()
        cache.clear()
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username="adminuser",
            email="admin@example.com",
            password="adminpass123",
        )
        self.user = User.objects.create_user(
            username="member",
            email="member@example.com",
            password="memberpass123",
        )

    def tearDown(self):
        cache.clear()
        self.override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def test_admin_index_contains_system_status_link_for_superuser(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("admin:system_status"))
        self.assertContains(response, "System Status")

    def test_system_status_page_requires_superuser(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("admin:system_status"))
        self.assertEqual(response.status_code, 302)

    def test_system_status_page_renders_for_superuser(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin:system_status"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Database Backup Status")
        self.assertContains(response, "Today Log Files")

    def test_system_status_context_includes_expected_sections(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin:system_status"))
        self.assertIn("log_statuses", response.context)
        self.assertIn("backup_files", response.context)
        self.assertIn("latest_backup_success", response.context)

    def test_audio_admin_actions_toggle_active_flag(self):
        audio = AudioPost.objects.create(
            uploaded_by=self.user,
            audio_file=SimpleUploadedFile("clip.mp3", b"ID3 audio", content_type="audio/mpeg"),
            music_name="Track",
            active=False,
        )
        model_admin = AudioPostAdmin(AudioPost, admin.site)
        queryset = AudioPost.objects.filter(pk=audio.pk)

        model_admin.actions[0](model_admin, None, queryset)
        audio.refresh_from_db()
        self.assertTrue(audio.active)

        model_admin.actions[1](model_admin, None, queryset)
        audio.refresh_from_db()
        self.assertFalse(audio.active)

    def test_audio_admin_preview_methods_render_expected_html(self):
        audio = AudioPost.objects.create(
            uploaded_by=self.user,
            audio_file=SimpleUploadedFile("clip.mp3", b"ID3 audio", content_type="audio/mpeg"),
            cover_image=SimpleUploadedFile("cover.jpg", b"fakejpeg", content_type="image/jpeg"),
            music_name="Track",
        )
        model_admin = AudioPostAdmin(AudioPost, admin.site)

        self.assertIn("<audio", model_admin.audio_preview(audio))
        self.assertIn("<img", model_admin.cover_preview(audio))

    def test_audio_admin_changelist_is_available_for_superuser(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin:blog_audiopost_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Audio posts")

    def test_audio_admin_change_page_is_available_for_superuser(self):
        audio = AudioPost.objects.create(
            uploaded_by=self.user,
            audio_file=SimpleUploadedFile("clip.mp3", b"ID3 audio", content_type="audio/mpeg"),
            music_name="Track",
        )
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin:blog_audiopost_change", args=[audio.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Track")

    def test_video_admin_preview_method_renders_expected_html(self):
        video = VideoPost.objects.create(
            uploaded_by=self.superuser,
            title="Video",
            description="Desc",
            video_file=SimpleUploadedFile("clip.mp4", b"video-bytes", content_type="video/mp4"),
        )
        model_admin = VideoPostAdmin(VideoPost, admin.site)

        self.assertIn("<video", model_admin.video_preview(video))

    def test_video_admin_changelist_is_available_for_superuser(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin:blog_videopost_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Video posts")

    def test_video_admin_change_page_is_available_for_superuser(self):
        video = VideoPost.objects.create(
            uploaded_by=self.superuser,
            title="Video",
            description="Desc",
            video_file=SimpleUploadedFile("clip.mp4", b"video-bytes", content_type="video/mp4"),
        )
        self.client.force_login(self.superuser)
        response = self.client.get(reverse("admin:blog_videopost_change", args=[video.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Video")
