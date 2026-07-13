import importlib
import os
from datetime import datetime
from pathlib import Path

from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings
from django.urls import path


class SettingsSplitTests(SimpleTestCase):
    def test_manage_defaults_to_dev_settings(self):
        manage_py = (self._base_dir() / "manage.py").read_text(encoding="utf-8")
        self.assertIn('my_site.settings.dev', manage_py)

    def test_dockerfile_defaults_to_prod_settings(self):
        dockerfile = (self._base_dir() / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("DJANGO_SETTINGS_MODULE=my_site.settings.prod", dockerfile)

    def test_compose_explicitly_sets_prod_settings_module(self):
        compose = (self._base_dir() / "docker-compose.yml").read_text(encoding="utf-8")
        self.assertIn("DJANGO_SETTINGS_MODULE: my_site.settings.dev", compose)

    def test_prod_compose_explicitly_sets_prod_settings_module(self):
        compose = (self._base_dir() / "docker-compose.prod.yml").read_text(encoding="utf-8")
        self.assertIn("DJANGO_SETTINGS_MODULE: my_site.settings.prod", compose)

    def test_settings_package_default_exports_dev_settings(self):
        settings_init = (self._base_dir() / "my_site" / "settings" / "__init__.py").read_text(encoding="utf-8")
        self.assertIn("from .dev import *", settings_init)

    @staticmethod
    def _base_dir():
        from pathlib import Path

        return Path(__file__).resolve().parent.parent.parent


class LoggingPolicyTests(SimpleTestCase):
    def test_runtime_dev_settings_keep_console_as_primary_log_sink(self):
        from django.conf import settings

        self.assertIn("console", settings.LOGGING["handlers"])
        self.assertIn("console", settings.LOGGING["loggers"]["django"]["handlers"])

    def test_dev_settings_enable_file_logging_for_local_debugging(self):
        dev_settings = importlib.import_module("my_site.settings.dev")

        self.assertIn("file", dev_settings.LOGGING["handlers"])
        self.assertIn("error_file", dev_settings.LOGGING["handlers"])
        self.assertIn("console", dev_settings.LOGGING["loggers"]["django"]["handlers"])
        self.assertIn("file", dev_settings.LOGGING["loggers"]["django.request"]["handlers"])
        self.assertIn("error_file", dev_settings.LOGGING["loggers"]["django.request"]["handlers"])
        self.assertEqual(
            dev_settings.LOGGING["handlers"]["file"]["class"],
            "my_site.logging_utils.DailyMonthlyFileHandler",
        )
        self.assertEqual(
            dev_settings.LOGGING["handlers"]["error_file"]["class"],
            "my_site.logging_utils.DailyMonthlyFileHandler",
        )
        self.assertEqual(dev_settings.LOGGING["handlers"]["error_file"]["level"], "WARNING")

    def test_prod_settings_enable_file_logging_and_console(self):
        prod_settings = importlib.import_module("my_site.settings.prod")

        self.assertIn("console", prod_settings.LOGGING["loggers"]["django"]["handlers"])
        self.assertIn("file", prod_settings.LOGGING["handlers"])
        self.assertIn("error_file", prod_settings.LOGGING["handlers"])

    def test_daily_monthly_file_handler_uses_month_folder_and_daily_filename(self):
        from my_site.logging_utils import DailyMonthlyFileHandler

        handler = DailyMonthlyFileHandler(log_dir=Path.cwd() / "logs", filename_prefix="django", delay=True)
        target_path = Path(handler.baseFilename)

        self.assertEqual(target_path.parent.name, datetime.now().strftime("%Y-%m"))
        self.assertEqual(target_path.name, f"django-{datetime.now().strftime('%Y-%m-%d')}.log")


class UploadLimitTests(SimpleTestCase):
    def test_default_upload_limits_are_more_realistic_for_media_workflows(self):
        from django.conf import settings

        self.assertGreaterEqual(settings.DATA_UPLOAD_MAX_MEMORY_SIZE, 25 * 1024 * 1024)
        self.assertGreaterEqual(settings.FILE_UPLOAD_MAX_MEMORY_SIZE, 25 * 1024 * 1024)

    def test_media_sync_defaults_are_configured(self):
        from django.conf import settings

        self.assertGreaterEqual(settings.MEDIA_SYNC_INTERVAL_SECONDS, 10)
        self.assertEqual(settings.MEDIA_SYNC_BEAT_MINUTES, 5)


class ProductionSecuritySettingsTests(SimpleTestCase):
    def test_prod_settings_force_debug_off(self):
        prod_settings = importlib.import_module("my_site.settings.prod")

        self.assertFalse(prod_settings.DEBUG)

    def test_prod_settings_default_to_https_and_secure_cookies(self):
        prod_source = (self._base_dir() / "my_site" / "settings" / "prod.py").read_text(encoding="utf-8")

        self.assertIn('SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)', prod_source)
        self.assertIn('SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=True, cast=bool)', prod_source)
        self.assertIn('CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=True, cast=bool)', prod_source)
        self.assertIn('SESSION_COOKIE_HTTPONLY = config("SESSION_COOKIE_HTTPONLY", default=True, cast=bool)', prod_source)
        self.assertIn('CSRF_COOKIE_HTTPONLY = config("CSRF_COOKIE_HTTPONLY", default=True, cast=bool)', prod_source)

    def test_prod_settings_default_to_hsts(self):
        prod_source = (self._base_dir() / "my_site" / "settings" / "prod.py").read_text(encoding="utf-8")

        self.assertIn('SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=31536000, cast=int)', prod_source)
        self.assertIn(
            'SECURE_HSTS_INCLUDE_SUBDOMAINS = config("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True, cast=bool)',
            prod_source,
        )
        self.assertIn(
            'SECURE_HSTS_PRELOAD = config("SECURE_HSTS_PRELOAD", default=True, cast=bool)',
            prod_source,
        )

    def test_prod_settings_use_secure_cookie_prefixes(self):
        prod_settings = importlib.import_module("my_site.settings.prod")

        self.assertTrue(prod_settings.SESSION_COOKIE_NAME.startswith("__Secure-"))
        self.assertTrue(prod_settings.CSRF_COOKIE_NAME.startswith("__Secure-"))

    def test_prod_settings_define_browser_protection_headers(self):
        prod_settings = importlib.import_module("my_site.settings.prod")

        self.assertEqual(prod_settings.SECURE_REFERRER_POLICY, "same-origin")
        self.assertTrue(prod_settings.SECURE_BROWSER_XSS_FILTER)
        self.assertEqual(prod_settings.SECURE_CROSS_ORIGIN_OPENER_POLICY, "same-origin")

    @staticmethod
    def _base_dir():
        return Path(__file__).resolve().parent.parent.parent


def _security_headers_probe_view(request):
    return HttpResponse("ok")


urlpatterns = [
    path("security-header-probe/", _security_headers_probe_view),
]


@override_settings(
    ROOT_URLCONF="my_site.tests.test_settings",
    SECURE_CONTENT_TYPE_NOSNIFF=True,
    X_FRAME_OPTIONS="DENY",
    SECURE_REFERRER_POLICY="same-origin",
    SECURE_SSL_REDIRECT=False,
    MIDDLEWARE=[
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
    ],
)
class SecurityHeadersRuntimeTests(SimpleTestCase):
    def test_security_middleware_sets_nosniff_header(self):
        response = self.client.get("/security-header-probe/")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")

    def test_security_middleware_sets_frame_options_header(self):
        response = self.client.get("/security-header-probe/")
        self.assertEqual(response["X-Frame-Options"], "DENY")

    def test_security_middleware_sets_referrer_policy_header(self):
        response = self.client.get("/security-header-probe/")
        self.assertEqual(response["Referrer-Policy"], "same-origin")



class IndexPortalTests(SimpleTestCase):
    def test_index_uses_blog_media_routes_instead_of_legacy_root_shortcuts(self):
        index_html = (self._base_dir() / "my_site" / "templates" / "index.html").read_text(encoding="utf-8")
        self.assertIn('href="/blog/gallery/"', index_html)
        self.assertIn('href="/blog/gallery/upload/"', index_html)
        self.assertIn('href="/blog/audio/list/"', index_html)
        self.assertNotIn('href="/gallery/"', index_html)



    def test_index_uses_default_font_and_portal_title(self):
        index_html = (self._base_dir() / "my_site" / "templates" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("fonts.googleapis.com/css2?family=Lobster&display=swap", index_html)
        self.assertIn('font-family: Georgia, "Times New Roman", serif;', index_html)
        self.assertIn("<title>my_site Portal</title>", index_html)

    @staticmethod
    def _base_dir():
        return Path(__file__).resolve().parent.parent.parent



class TemplateStructureTests(SimpleTestCase):
    def test_template_dirs_use_project_template_directory(self):
        base_settings = (self._base_dir() / "my_site" / "settings" / "base.py").read_text(encoding="utf-8")
        self.assertIn('BASE_DIR / "my_site" / "templates"', base_settings)
        self.assertNotIn('"DIRS": [BASE_DIR]', base_settings)

    def test_site_index_template_lives_under_project_templates(self):
        template_path = self._base_dir() / "my_site" / "templates" / "index.html"
        self.assertTrue(template_path.exists())

    @staticmethod
    def _base_dir():
        return Path(__file__).resolve().parent.parent.parent
