from pathlib import Path
import unittest


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class LoggingConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.compose = (BASE_DIR / "docker-compose.prod.yml").read_text(encoding="utf-8")
        self.nginx = (BASE_DIR / "nginx.prod.conf").read_text(encoding="utf-8")

    def test_nginx_logs_are_mounted_to_project_logs(self):
        self.assertIn("./logs/nginx-access:/var/log/nginx-access", self.compose)
        self.assertIn("./logs/nginx-error:/var/log/nginx-error", self.compose)
        self.assertIn("access_log /var/log/nginx-access/access.log;", self.nginx)
        self.assertIn("error_log /var/log/nginx-error/error.log warn;", self.nginx)

    def test_celery_service_uses_inline_celery_command(self):
        self.assertIn("celery -A my_site worker -l info -E --concurrency=1", self.compose)

    def test_runtime_log_policy_controls_log_systems(self):
        policy = (BASE_DIR / "my_site" / "logging_policy.py").read_text(encoding="utf-8")
        for prefix in ["celery", "nginx-access", "nginx-error", "gunicorn-access", "gunicorn-error", "django", "django-error"]:
            with self.subTest(prefix=prefix):
                self.assertIn(f'"{prefix}"', policy)
        self.assertIn("RUNTIME_LOG_RETENTION_DAYS = 120", policy)


class AdminConvenienceConfigurationTests(unittest.TestCase):
    def test_admin_files_include_fast_search_filter_and_inline_editing(self):
        blog_admin = (BASE_DIR / "blog" / "admin.py").read_text(encoding="utf-8")
        users_admin = (BASE_DIR / "users" / "admin.py").read_text(encoding="utf-8")
        images_admin = (BASE_DIR / "images" / "admin.py").read_text(encoding="utf-8")

        self.assertIn('search_fields = ["title", "body"]', blog_admin)
        self.assertIn('list_filter = ["status", "created", "publish", "author"]', blog_admin)
        self.assertIn('prepopulated_fields = {"slug": ("title",)}', blog_admin)
        self.assertIn("class UserAdmin(DjangoUserAdmin):", users_admin)
        self.assertIn("class TokenAdmin(admin.ModelAdmin):", users_admin)
        self.assertIn('list_editable = ["is_active"]', users_admin)
        self.assertIn('readonly_fields = ["thumbnail_preview", "created", "updated"]', images_admin)
        self.assertIn('readonly_fields = ["cover_preview", "gallery_preview", "created", "updated"]', images_admin)


if __name__ == "__main__":
    unittest.main()
