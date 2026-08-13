from pathlib import Path
import shutil
import subprocess

from django.test import SimpleTestCase


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class DevDockerComposeFileTests(SimpleTestCase):
    def setUp(self):
        self.compose_path = BASE_DIR / "docker-compose.dev.yml"
        self.compose_text = self.compose_path.read_text(encoding="utf-8")
        self.dev_env_path = BASE_DIR / ".env.dev"
        self.dev_env_text = self.dev_env_path.read_text(encoding="utf-8")

    def test_dev_compose_targets_dev_layout(self):
        """环境变量通过 .env.dev 注入，Dockerfile 使用 Dockerfile.dev"""
        self.assertIn("DJANGO_SETTINGS_MODULE=my_site.settings.dev", self.dev_env_text)
        self.assertIn("dockerfile: Dockerfile.dev", self.compose_text)

    def test_dev_compose_defines_expected_services(self):
        self.assertIn("services:", self.compose_text)
        self.assertIn("db:", self.compose_text)
        self.assertIn("web:", self.compose_text)
        self.assertIn("celery:", self.compose_text)
        self.assertIn("celery-beat:", self.compose_text)
        self.assertNotIn("nginx:", self.compose_text)

    def test_dev_db_service_uses_postgres_16(self):
        self.assertIn("image: postgres:16", self.compose_text)

    def test_dev_db_service_has_healthcheck(self):
        self.assertIn("healthcheck:", self.compose_text)
        self.assertIn("pg_isready -U ${DB_USER} -d ${DB_NAME}", self.compose_text)

    def test_dev_redis_and_celery_services_have_healthchecks(self):
        self.assertIn('test: ["CMD", "redis-cli", "ping"]', self.compose_text)
        self.assertIn("inspect', 'ping'", self.compose_text)
        self.assertIn("cmdline = Path('/proc/1/cmdline')", self.compose_text)

    def test_dev_web_service_uses_local_wheel_contexts(self):
        self.assertIn("additional_contexts:", self.compose_text)
        self.assertIn("linux_wheels: G:/Projects/Linux_Python_Packages", self.compose_text)
        self.assertNotIn("docker_packages: G:/Projects/Docker_Packages", self.compose_text)

    def test_dev_web_service_uses_env_file_for_settings(self):
        """环境变量通过 .env.dev 注入，而非写在 compose 的 environment 块中"""
        self.assertIn("env_file:\n      - .env.dev", self.compose_text)
        self.assertIn("DB_NAME=my_site_db", self.dev_env_text)
        self.assertIn("DB_USER=my_site_user", self.dev_env_text)
        self.assertIn("DB_PASSWORD=", self.dev_env_text)
        self.assertIn("DB_HOST=db", self.dev_env_text)
        self.assertIn("DB_PORT=5432", self.dev_env_text)

    def test_dev_web_service_mounts_project_code_static_media_and_backups(self):
        self.assertIn("- .:/code", self.compose_text)
        self.assertIn("- ./staticfiles:/code/staticfiles", self.compose_text)
        self.assertIn("- ./media:/code/media", self.compose_text)
        self.assertIn("- ./backups:/code/backups", self.compose_text)

    def test_dev_web_service_has_healthcheck(self):
        self.assertIn("urllib.request.Request('http://127.0.0.1:8000/health/'", self.compose_text)
        self.assertIn("exit(0 if r.status == 200 else 1)", self.compose_text)
        self.assertIn("'X-Forwarded-Proto': 'https'", self.compose_text)

    def test_dev_compose_declares_named_volumes(self):
        self.assertIn("volumes:", self.compose_text)
        self.assertIn("postgres_data:", self.compose_text)
        self.assertIn("elasticsearch_data:", self.compose_text)

    def test_dev_compose_config_is_valid_when_docker_is_available(self):
        docker = shutil.which("docker")
        if docker is None:
            self.skipTest("docker is not installed in this environment")
        result = subprocess.run(
            [docker, "compose", "-f", "docker-compose.dev.yml", "config"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("services:", result.stdout)

    def test_dev_compose_service_list_is_valid_when_docker_is_available(self):
        docker = shutil.which("docker")
        if docker is None:
            self.skipTest("docker is not installed in this environment")
        result = subprocess.run(
            [docker, "compose", "-f", "docker-compose.dev.yml", "config", "--services"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("db", result.stdout)
        self.assertIn("web", result.stdout)
        self.assertIn("celery", result.stdout)
        self.assertIn("celery-beat", result.stdout)
        self.assertNotIn("nginx", result.stdout)
