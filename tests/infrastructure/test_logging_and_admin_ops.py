from pathlib import Path
import unittest


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class LoggingConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.compose = (BASE_DIR / "docker-compose.prod.yml").read_text(encoding="utf-8")
        self.nginx = (BASE_DIR / "nginx.prod.conf").read_text(encoding="utf-8")
        self.celery_script = (BASE_DIR / "scripts" / "celery_with_daily_log.sh").read_text(encoding="utf-8")

    def test_nginx_logs_are_mounted_to_project_logs(self):
        self.assertIn("./logs/nginx:/var/log/nginx", self.compose)
        self.assertIn("access_log /var/log/nginx/access.log;", self.nginx)
        self.assertIn("error_log /var/log/nginx/error.log warn;", self.nginx)
        self.assertIn("access_log /var/log/nginx/ssl-access.log;", self.nginx)
        self.assertIn("error_log /var/log/nginx/ssl-error.log warn;", self.nginx)

    def test_celery_services_use_daily_log_wrapper(self):
        self.assertIn("scripts/celery_with_daily_log.sh celery", self.compose)
        self.assertIn("runtime_log_router.py", self.celery_script)

    def test_runtime_log_policy_controls_six_log_systems(self):
        policy = (BASE_DIR / "my_site" / "logging_policy.py").read_text(encoding="utf-8")
        for prefix in ["celery", "nginx", "gunicorn-access", "gunicorn-error", "django", "error"]:
            with self.subTest(prefix=prefix):
                self.assertIn(f'"{prefix}"', policy)
        self.assertIn("RUNTIME_LOG_RETENTION_DAYS = 120", policy)


class AdminConvenienceConfigurationTests(unittest.TestCase):
    def test_admin_files_include_fast_search_filter_and_inline_editing(self):
        blog_admin = (BASE_DIR / "blog" / "admin.py").read_text(encoding="utf-8")
        users_admin = (BASE_DIR / "users" / "admin.py").read_text(encoding="utf-8")
        images_admin = (BASE_DIR / "images" / "admin.py").read_text(encoding="utf-8")

        self.assertIn('search_fields = ["title", "body", "slug", "author__username", "tags__name"]', blog_admin)
        self.assertIn('list_editable = ["status"]', blog_admin)
        self.assertIn('actions = ["make_published", "make_draft"]', blog_admin)
        self.assertIn("class UserAdmin(DjangoUserAdmin):", users_admin)
        self.assertIn("class TokenAdmin(admin.ModelAdmin):", users_admin)
        self.assertIn('list_editable = ["is_active"]', users_admin)
        self.assertIn('"thumbnail_preview", "title"', images_admin)
        self.assertIn('"cover_preview", "title"', images_admin)


if __name__ == "__main__":
    unittest.main()
