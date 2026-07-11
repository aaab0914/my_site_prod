import shutil
import subprocess

from django.test import SimpleTestCase

from .common import BASE_DIR


class GunicornContainerConfigTests(SimpleTestCase):
    def setUp(self):
        self.dockerfile = (BASE_DIR / "Dockerfile").read_text(encoding="utf-8")
        self.entrypoint = (BASE_DIR / "entrypoint.sh").read_text(encoding="utf-8")

    def test_dockerfile_exposes_gunicorn_port(self):
        self.assertIn("EXPOSE 8000", self.dockerfile)

    def test_entrypoint_starts_gunicorn(self):
        self.assertIn("exec gunicorn", self.entrypoint)
        self.assertIn("--bind 0.0.0.0:8000", self.entrypoint)
        self.assertIn("my_site.wsgi:application", self.entrypoint)

    def test_entrypoint_runs_preflight_steps(self):
        self.assertIn("python manage.py check --deploy", self.entrypoint)
        self.assertIn("python manage.py collectstatic --noinput", self.entrypoint)

    def test_dockerfile_uses_stable_entrypoint_path_outside_bind_mount(self):
        self.assertIn("COPY entrypoint.sh /usr/local/bin/entrypoint.sh", self.dockerfile)
        self.assertIn('ENTRYPOINT ["sh", "/usr/local/bin/entrypoint.sh"]', self.dockerfile)

    def test_gunicorn_command_uses_expected_worker_and_bind_settings(self):
        self.assertIn("--workers 2", self.entrypoint)
        self.assertIn("--bind 0.0.0.0:8000", self.entrypoint)

    def test_gunicorn_configuration_is_valid_when_gunicorn_is_installed(self):
        gunicorn = shutil.which("gunicorn")
        if gunicorn is None:
            self.skipTest("gunicorn is not installed in this environment")
        result = subprocess.run(
            [gunicorn, "--check-config", "--workers", "2", "--bind", "0.0.0.0:8000", "my_site.wsgi:application"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
