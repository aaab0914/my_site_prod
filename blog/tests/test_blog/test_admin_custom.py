import shutil
import tempfile

from django.contrib import admin
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse



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

