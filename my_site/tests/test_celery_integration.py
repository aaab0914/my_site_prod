from pathlib import Path
import shutil
import subprocess

from django.test import SimpleTestCase, TestCase, override_settings

from blog.tasks import ping_blog_task
from my_site.tasks import sync_site_media_task


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class CeleryIntegrationTests(TestCase):
    def setUp(self):
        self.base_settings = (BASE_DIR / "my_site" / "settings" / "base.py").read_text(encoding="utf-8")
        self.compose = (BASE_DIR / "docker-compose.yml").read_text(encoding="utf-8")

    def test_celery_integration_is_configured_for_events_and_scheduling(self):
        self.assertIn('command: celery -A my_site worker -l info -E', self.compose)
        self.assertIn('command: celery -A my_site beat -l info', self.compose)
        self.assertIn('CELERY_WORKER_SEND_TASK_EVENTS = config("CELERY_WORKER_SEND_TASK_EVENTS"', self.base_settings)
        self.assertIn('CELERY_TASK_SEND_SENT_EVENT = config("CELERY_TASK_SEND_SENT_EVENT"', self.base_settings)
        self.assertIn('CELERY_TASK_TRACK_STARTED = True', self.base_settings)
        self.assertIn('crontab(minute="*/5")', self.base_settings)
        self.assertIn('MEDIA_SYNC_BEAT_MINUTES = config("MEDIA_SYNC_BEAT_MINUTES", default=5, cast=int)', self.base_settings)
        self.assertIn('"task": "my_site.tasks.sync_site_media_task"', self.base_settings)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
    def test_celery_task_executes_successfully_in_eager_mode(self):
        result = ping_blog_task.delay()
        self.assertTrue(result.successful())
        self.assertEqual(result.get(), "blog-task-ok")

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
    def test_media_sync_task_executes_successfully_in_eager_mode(self):
        result = sync_site_media_task.delay()
        self.assertTrue(result.successful())
        self.assertIn("missing_actions", result.get())
        self.assertIn("trashed_files", result.get())

    def test_celery_worker_replies_to_inspect_ping_when_running(self):
        docker = shutil.which("docker")
        if docker is None:
            self.skipTest("docker is not installed in this environment")

        result = subprocess.run(
            [
                docker,
                "compose",
                "exec",
                "-T",
                "celery",
                "celery",
                "-A",
                "my_site",
                "inspect",
                "ping",
            ],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 0, msg=output)
        self.assertIn("pong", output)
