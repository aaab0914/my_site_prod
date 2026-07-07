from pathlib import Path
from unittest.mock import Mock, patch

from django.test import SimpleTestCase


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class SentryIntegrationTests(SimpleTestCase):
    def setUp(self):
        self.base_settings = (BASE_DIR / "my_site" / "settings" / "base.py").read_text(encoding="utf-8")

    def test_sentry_integration_includes_django_and_celery(self):
        self.assertIn("from sentry_sdk.integrations.celery import CeleryIntegration", self.base_settings)
        self.assertIn("from sentry_sdk.integrations.django import DjangoIntegration", self.base_settings)
        self.assertIn("SENTRY_DSN = config(", self.base_settings)
        self.assertIn("integrations=[DjangoIntegration(), CeleryIntegration()]", self.base_settings)
        self.assertIn("sentry_sdk.init(", self.base_settings)

    def test_sentry_sdk_init_receives_django_and_celery_integrations(self):
        django_integration = object()
        celery_integration = object()
        fake_config = Mock(side_effect=lambda key, default="", cast=None: {
            "SECRET_KEY": "test-secret",
            "ALLOWED_HOSTS": ["localhost", "127.0.0.1"],
            "CSRF_TRUSTED_ORIGINS": "",
            "REDIS_URL": "redis://redis:6379/0",
            "CELERY_BROKER_URL": "redis://redis:6379/0",
            "CELERY_RESULT_BACKEND": "redis://redis:6379/0",
            "ELASTICSEARCH_URL": "http://elasticsearch:9200",
            "STATIC_ROOT": str(BASE_DIR / "staticfiles"),
            "SENTRY_DSN": "https://examplePublicKey@o0.ingest.sentry.io/0",
            "SENTRY_TRACES_SAMPLE_RATE": "0.5",
            "SENTRY_PROFILES_SAMPLE_RATE": "0.1",
        }.get(key, default))

        with patch("decouple.config", fake_config), \
             patch("sentry_sdk.init") as sentry_init, \
             patch("sentry_sdk.integrations.django.DjangoIntegration", return_value=django_integration), \
             patch("sentry_sdk.integrations.celery.CeleryIntegration", return_value=celery_integration):
            import importlib
            import my_site.settings.base as base_module

            importlib.reload(base_module)

        sentry_init.assert_called_once()
        integrations = sentry_init.call_args.kwargs["integrations"]
        self.assertEqual(integrations, [django_integration, celery_integration])

    def test_sentry_capture_exception_is_called_for_runtime_error(self):
        with patch("sentry_sdk.capture_exception") as capture_exception:
            try:
                raise RuntimeError("sentry-runtime-check")
            except RuntimeError as exc:
                import sentry_sdk

                sentry_sdk.capture_exception(exc)

        capture_exception.assert_called_once()
        self.assertIsInstance(capture_exception.call_args.args[0], RuntimeError)

    def test_sentry_sdk_current_scope_can_capture_task_exception(self):
        with patch("sentry_sdk.Scope.capture_exception") as capture_exception:
            import sentry_sdk

            try:
                raise ValueError("celery-task-failure")
            except ValueError as exc:
                sentry_sdk.get_current_scope().capture_exception(exc)

        capture_exception.assert_called_once()
        self.assertIsInstance(capture_exception.call_args.args[0], ValueError)
