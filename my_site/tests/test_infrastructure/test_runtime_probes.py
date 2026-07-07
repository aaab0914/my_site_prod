import shutil
import subprocess
from urllib.error import URLError
from urllib.request import urlopen

from django.test import SimpleTestCase

from .common import BASE_DIR


class FilesystemPermissionSafetyTests(SimpleTestCase):
    def setUp(self):
        self.compose = (BASE_DIR / "docker-compose.yml").read_text(encoding="utf-8")
        self.dockerfile = (BASE_DIR / "Dockerfile").read_text(encoding="utf-8")
        self.entrypoint = (BASE_DIR / "entrypoint.sh").read_text(encoding="utf-8")

    def test_web_service_bind_mounts_project_code(self):
        self.assertIn("- .:/code", self.compose)

    def test_bind_mount_risk_is_mitigated_by_external_entrypoint_location(self):
        self.assertIn("COPY entrypoint.sh /usr/local/bin/entrypoint.sh", self.dockerfile)
        self.assertNotIn('ENTRYPOINT ["/code/entrypoint.sh"]', self.dockerfile)

    def test_entrypoint_repairs_runtime_permissions_for_writable_directories(self):
        self.assertIn("chown -R app:app /code", self.entrypoint)
        self.assertIn("chmod -R 755 /code/media /code/logs", self.entrypoint)

    def test_entrypoint_runs_production_env_validation(self):
        self.assertIn("python /code/validate_prod_env.py", self.entrypoint)


class DockerRuntimeProbeTests(SimpleTestCase):
    def test_docker_binary_is_available_when_runtime_checks_are_requested(self):
        if shutil.which("docker") is None:
            self.skipTest("docker is not installed in this environment")

    def test_docker_compose_config_command_succeeds_when_docker_is_available(self):
        docker = shutil.which("docker")
        if docker is None:
            self.skipTest("docker is not installed in this environment")
        result = subprocess.run([docker, "compose", "config"], cwd=BASE_DIR, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("services:", result.stdout)

    def test_compose_declares_expected_services(self):
        docker = shutil.which("docker")
        if docker is None:
            self.skipTest("docker is not installed in this environment")
        result = subprocess.run(
            [docker, "compose", "config", "--services"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("db", result.stdout)
        self.assertIn("web", result.stdout)
        self.assertIn("nginx", result.stdout)

    def test_nginx_serves_blog_route_when_stack_is_running(self):
        docker = shutil.which("docker")
        if docker is None:
            self.skipTest("docker is not installed in this environment")
        ps_result = subprocess.run(
            [docker, "compose", "ps", "--services", "--status", "running"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if ps_result.returncode != 0:
            self.skipTest(ps_result.stderr.strip() or "docker compose ps failed")
        if "nginx" not in ps_result.stdout:
            self.skipTest("nginx service is not running")
        try:
            response = urlopen("http://127.0.0.1/blog/", timeout=10)
        except URLError as exc:
            self.fail(f"nginx blog route probe failed: {exc}")
        self.assertGreaterEqual(response.status, 200)
        self.assertLess(response.status, 500)
