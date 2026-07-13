import os
import shutil
import tempfile
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import SimpleTestCase, TestCase, override_settings

from images.models import ImagePost
from my_site.logging_utils import DailyMonthlyFileHandler
from my_site.media_cleanup import move_media_file_to_trash
from my_site.media_sync import sync_site_media
from my_site.request_context import reset_current_request, set_current_request
from my_site.tasks import purge_old_runtime_logs_task, sync_site_media_task


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class DatabaseBackupSystemTests(SimpleTestCase):
    def test_backup_script_uses_single_prod_compose_entrypoint(self):
        script = (BASE_DIR / "backup_db.sh").read_text(encoding="utf-8")

        self.assertIn('COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"', script)
        self.assertIn('LOG_FILE="$PROJECT_DIR/logs/backup.log"', script)
        self.assertIn('BACKUP_DIR="$PROJECT_DIR/backups/db"', script)
        self.assertIn('docker || command -v docker.exe', script)
        self.assertNotIn("backup_loop.sh", script)


class LoggingSystemTests(SimpleTestCase):
    def test_daily_monthly_log_handler_writes_into_single_logs_tree(self):
        handler = DailyMonthlyFileHandler(log_dir=BASE_DIR / "logs", filename_prefix="django", delay=True)
        target_path = Path(handler.baseFilename)

        self.assertEqual(target_path.parents[1], BASE_DIR / "logs")
        self.assertRegex(target_path.parent.name, r"^\d{4}-\d{2}$")
        self.assertTrue(target_path.name.startswith("django-"))
        self.assertTrue(target_path.name.endswith(".log"))

    def test_long_run_scripts_exist(self):
        self.assertTrue((BASE_DIR / "scripts" / "runtime_self_check.py").exists())
        self.assertTrue((BASE_DIR / "scripts" / "long_run_check.py").exists())

    def test_runtime_self_check_script_references_both_compose_files(self):
        script = (BASE_DIR / "scripts" / "runtime_self_check.py").read_text(encoding="utf-8")
        self.assertIn("docker-compose.yml", script)
        self.assertIn("docker-compose.prod.yml", script)

    def test_long_run_check_script_reports_json(self):
        script = (BASE_DIR / "scripts" / "long_run_check.py").read_text(encoding="utf-8")
        self.assertIn("json.dumps(report", script)

    @override_settings(BASE_DIR=BASE_DIR)
    def test_purge_old_runtime_logs_task_deletes_only_old_logs(self):
        old_dir = BASE_DIR / "logs" / "1999-01"
        old_dir.mkdir(parents=True, exist_ok=True)
        old_file = old_dir / "django-1999-01-01.log"
        old_file.write_text("old", encoding="utf-8")
        old_timestamp = 946684800
        os.utime(old_file, (old_timestamp, old_timestamp))

        result = purge_old_runtime_logs_task(days=1)

        self.assertFalse(old_file.exists())
        self.assertGreaterEqual(result["deleted_files"], 1)


@override_settings(MEDIA_SYNC_ENABLED=False)
class MediaSyncSystemTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp(prefix="media-sync-workflow-")
        self.override = override_settings(MEDIA_ROOT=self.media_root)
        self.override.enable()
        self.user = get_user_model().objects.create_user(username="media-workflow-user", password="secret123")

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

        trash_root = Path(settings.BASE_DIR) / ".trash"
        if trash_root.exists():
            shutil.rmtree(trash_root, ignore_errors=True)

    def _browser_request(self, path="/media-delete/"):
        return type("Request", (), {"method": "POST", "path": path})()

    def test_automatic_media_sync_entrypoints_are_disabled(self):
        result = sync_site_media()
        task_result = sync_site_media_task()

        self.assertFalse(result["enabled"])
        self.assertIn("only when users delete objects", result["reason"])
        self.assertFalse(task_result["enabled"])

    def test_media_file_only_moves_to_trash_for_browser_delete_requests(self):
        relative_name = "posts/2026/07/13/probe.jpg"
        file_path = Path(self.media_root) / relative_name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(b"probe-image")

        self.assertIsNone(move_media_file_to_trash(relative_name))
        self.assertTrue(file_path.exists())

        token = set_current_request(self._browser_request())
        try:
            trashed_to = move_media_file_to_trash(relative_name)
        finally:
            reset_current_request(token)

        self.assertIsNotNone(trashed_to)
        self.assertFalse(file_path.exists())
        self.assertTrue((Path(settings.BASE_DIR) / trashed_to).exists())

    def test_model_delete_moves_media_file_to_trash_via_signal_for_browser_requests(self):
        image = ImagePost.objects.create(title="signal-delete", uploaded_by=self.user)
        image.image.save("signal-delete.png", ContentFile(b"image-bytes"), save=True)

        original_path = Path(self.media_root) / image.image.name
        self.assertTrue(original_path.exists())

        token = set_current_request(self._browser_request("/images/delete/"))
        try:
            image.delete()
        finally:
            reset_current_request(token)

        self.assertFalse(original_path.exists())
        moved_files = list((Path(settings.BASE_DIR) / ".trash").rglob("signal-delete.png"))
        self.assertTrue(moved_files)
