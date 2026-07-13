from pathlib import Path

from django.test import SimpleTestCase


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class AuditLoggingContractTests(SimpleTestCase):
    def setUp(self):
        self.audit_middleware = (BASE_DIR / "my_site" / "audit_middleware.py").read_text(encoding="utf-8")
        self.base_settings = (BASE_DIR / "my_site" / "settings" / "base.py").read_text(encoding="utf-8")
        self.delete_guards = (BASE_DIR / "my_site" / "delete_guards.py").read_text(encoding="utf-8")
        self.runtime_file_guards = (BASE_DIR / "my_site" / "runtime_file_guards.py").read_text(encoding="utf-8")

    def test_audit_middleware_is_enabled_in_base_settings(self):
        self.assertIn('"my_site.audit_middleware.AuditLoggingMiddleware"', self.base_settings)

    def test_audit_middleware_persists_core_request_fields(self):
        self.assertIn("AuditLog.objects.create(", self.audit_middleware)
        self.assertIn("method=request.method", self.audit_middleware)
        self.assertIn("path=request.path", self.audit_middleware)
        self.assertIn("status_code=response.status_code", self.audit_middleware)
        self.assertIn("response_time=response_time", self.audit_middleware)

    def test_audit_logs_cannot_be_deleted_outside_browser_requests(self):
        self.assertIn("enforce_browser_delete_only", self.delete_guards)
        self.assertIn("sender=AuditLog", self.delete_guards)

    def test_runtime_file_guard_blocks_database_and_log_file_deletes(self):
        self.assertIn('PROTECTED_RUNTIME_ROOT_NAMES = ("logs", "backups")', self.runtime_file_guards)
        self.assertIn("PROTECTED_DATABASE_PATH_PARTS", self.runtime_file_guards)
        self.assertIn("is_protected_runtime_path", self.runtime_file_guards)
        self.assertIn("ensure_runtime_file_not_protected", self.runtime_file_guards)
        self.assertIn("PermissionDenied", self.runtime_file_guards)


class MediaCleanupContractTests(SimpleTestCase):
    def setUp(self):
        self.cleanup = (BASE_DIR / "my_site" / "media_cleanup.py").read_text(encoding="utf-8")
        self.signals = (BASE_DIR / "my_site" / "media_signals.py").read_text(encoding="utf-8")
        self.sync = (BASE_DIR / "my_site" / "media_sync.py").read_text(encoding="utf-8")
        self.gallery_sync = (BASE_DIR / "images" / "sync.py").read_text(encoding="utf-8")
        self.request_context = (BASE_DIR / "my_site" / "request_context.py").read_text(encoding="utf-8")

    def test_media_cleanup_requires_browser_delete_request_before_trash_move(self):
        self.assertIn("is_browser_delete_request", self.cleanup)
        self.assertIn("if not is_browser_delete_request()", self.cleanup)
        self.assertIn("ensure_runtime_file_not_protected", self.cleanup)
        self.assertIn('Path(settings.BASE_DIR) / ".trash" / timestamp', self.cleanup)
        self.assertIn("shutil.move", self.cleanup)

    def test_media_signals_only_move_files_for_browser_triggered_deletes(self):
        self.assertIn("from .media_cleanup import cleanup_instance_media_files, prepare_instance_media_cleanup", self.signals)
        self.assertIn("prepare_instance_media_cleanup(instance)", self.signals)
        self.assertIn("cleanup_instance_media_files(instance)", self.signals)

    def test_media_sync_system_is_read_only_and_never_deletes_files_or_records(self):
        self.assertNotIn("instance.delete()", self.sync)
        self.assertNotIn("move_media_file_to_trash", self.sync)
        self.assertIn("missing_file_detected_no_delete", self.sync)
        self.assertIn('"trashed_files": []', self.sync)
        self.assertIn("script_delete_blocked", self.sync)

    def test_gallery_sync_is_read_only_and_never_deletes_files_or_records(self):
        self.assertNotIn(".delete()", self.gallery_sync)
        self.assertNotIn("move_media_file_to_trash", self.gallery_sync)
        self.assertIn('"deleted_records"', self.gallery_sync)
        self.assertIn('result.get("trashed_files", [])', self.gallery_sync)

    def test_request_context_tracks_current_http_request_for_delete_guarding(self):
        self.assertIn("ContextVar", self.request_context)
        self.assertIn('return request.method in {"POST", "DELETE"}', self.request_context)


class BackupSystemContractTests(SimpleTestCase):
    def setUp(self):
        self.entrypoint = (BASE_DIR / "entrypoint.sh").read_text(encoding="utf-8")
        self.dev_compose = (BASE_DIR / "docker-compose.yml").read_text(encoding="utf-8")
        self.prod_compose = (BASE_DIR / "docker-compose.prod.yml").read_text(encoding="utf-8")

    def test_backup_storage_is_mounted_but_not_started_from_container_entrypoint(self):
        self.assertIn("./backups:/code/backups", self.dev_compose)
        self.assertIn("./backups:/code/backups", self.prod_compose)
        self.assertIn("skipping in-container backup loop", self.entrypoint)


class SiteBootstrapContractTests(SimpleTestCase):
    def setUp(self):
        self.blog_app = (BASE_DIR / "blog" / "apps.py").read_text(encoding="utf-8")
        self.site_bootstrap = (BASE_DIR / "my_site" / "site_bootstrap.py").read_text(encoding="utf-8")

    def test_startup_ensures_default_django_site_record_exists(self):
        self.assertIn("ensure_default_site()", self.blog_app)
        self.assertIn("Site.objects.update_or_create", self.site_bootstrap)
        self.assertIn("settings.SITE_ID", self.site_bootstrap)
        self.assertIn("localhost:8000", self.site_bootstrap)
