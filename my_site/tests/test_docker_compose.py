from pathlib import Path
import os
import shutil
import subprocess

from django.test import SimpleTestCase


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class DockerComposeFileTests(SimpleTestCase):
    def setUp(self):
        self.prod_compose_path = BASE_DIR / "docker-compose.prod.yml"
        self.prod_compose_text = self.prod_compose_path.read_text(encoding="utf-8")
        self.prod_env_path = BASE_DIR / ".env.prod"
        self.prod_env_text = self.prod_env_path.read_text(encoding="utf-8")
        self.readme_path = BASE_DIR / "README.md"
        self.readme_text = self.readme_path.read_text(encoding="utf-8")

    def test_prod_compose_targets_prod_layout(self):
        """环境变量通过 .env.prod 注入，Dockerfile 使用 Dockerfile.prod"""
        self.assertIn("DJANGO_SETTINGS_MODULE=my_site.settings.prod", self.prod_env_text)
        self.assertIn("dockerfile: Dockerfile.prod", self.prod_compose_text)

    def test_prod_compose_defines_expected_services(self):
        self.assertIn("services:", self.prod_compose_text)
        self.assertIn("db:", self.prod_compose_text)
        self.assertIn("web:", self.prod_compose_text)
        self.assertIn("nginx:", self.prod_compose_text)

    def test_prod_db_service_uses_postgres_16(self):
        self.assertIn("image: postgres:16", self.prod_compose_text)

    def test_prod_db_service_has_healthcheck(self):
        self.assertIn("healthcheck:", self.prod_compose_text)
        self.assertIn("pg_isready -U ${DB_USER} -d ${DB_NAME}", self.prod_compose_text)

    def test_prod_redis_and_celery_services_have_healthchecks(self):
        self.assertIn('test: ["CMD", "redis-cli", "ping"]', self.prod_compose_text)
        self.assertIn("inspect', 'ping'", self.prod_compose_text)
        self.assertIn("cmdline = Path('/proc/1/cmdline')", self.prod_compose_text)

    def test_prod_web_service_builds_from_dockerfile_prod(self):
        self.assertIn("dockerfile: Dockerfile.prod", self.prod_compose_text)

    def test_prod_web_service_uses_env_file_for_settings(self):
        """环境变量通过 .env.prod 注入，而非写在 compose 的 environment 块中"""
        self.assertIn("env_file:\n      - .env.prod", self.prod_compose_text)
        self.assertIn("DB_NAME=my_site_db", self.prod_env_text)
        self.assertIn("DB_USER=my_site_user", self.prod_env_text)
        self.assertIn("DB_PASSWORD=", self.prod_env_text)
        self.assertIn("DB_HOST=db", self.prod_env_text)
        self.assertIn("DB_PORT=5432", self.prod_env_text)

    def test_prod_web_service_mounts_static_media_and_backups(self):
        self.assertIn("- ./staticfiles:/code/staticfiles", self.prod_compose_text)
        self.assertIn("- ./media:/code/media", self.prod_compose_text)
        self.assertIn("- ./backups:/code/backups", self.prod_compose_text)

    def test_prod_web_service_has_healthcheck(self):
        self.assertIn("urllib.request.Request('http://127.0.0.1:8000/health/'", self.prod_compose_text)
        self.assertIn("exit(0 if r.status == 200 else 1)", self.prod_compose_text)
        self.assertIn("'X-Forwarded-Proto': 'https'", self.prod_compose_text)

    def test_nginx_service_mounts_expected_files(self):
        self.assertIn("./nginx.prod.conf:/etc/nginx/conf.d/default.conf:ro", self.prod_compose_text)
        self.assertIn("./staticfiles:/static:ro", self.prod_compose_text)
        self.assertIn("./media:/media:ro", self.prod_compose_text)

    def test_prod_compose_declares_named_volumes(self):
        self.assertIn("volumes:", self.prod_compose_text)
        self.assertIn("postgres_data:", self.prod_compose_text)
        self.assertIn("elasticsearch_data:", self.prod_compose_text)

    def test_production_compose_does_not_bind_mount_project_code(self):
        self.assertNotIn("- .:/code", self.prod_compose_text)
        self.assertNotIn("/code:ro", self.prod_compose_text)

    def test_readme_documents_prod_compose_usage(self):
        self.assertIn("docker compose -f docker-compose.prod.yml up -d --build", self.readme_text)
        self.assertIn("docker compose -f docker-compose.prod.yml exec web python manage.py migrate", self.readme_text)
        self.assertIn("docker compose -f docker-compose.prod.yml exec web python manage.py test", self.readme_text)

    def test_compose_config_is_valid_when_docker_is_available(self):
        docker = shutil.which("docker")
        if docker is None:
            self.skipTest("docker is not installed in this environment")

        result = subprocess.run(
            [docker, "compose", "-f", "docker-compose.prod.yml", "config"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("services:", result.stdout)

    def test_prod_compose_service_list_is_valid_when_docker_is_available(self):
        docker = shutil.which("docker")
        if docker is None:
            self.skipTest("docker is not installed in this environment")

        result = subprocess.run(
            [docker, "compose", "-f", "docker-compose.prod.yml", "config", "--services"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("db", result.stdout)
        self.assertIn("web", result.stdout)
        self.assertIn("nginx", result.stdout)

    def test_production_compose_config_is_valid_with_ci_env_when_docker_is_available(self):
        docker = shutil.which("docker")
        if docker is None:
            self.skipTest("docker is not installed in this environment")

        env = os.environ.copy()
        env.setdefault("DB_NAME", "my_site_db")
        env.setdefault("DB_USER", "my_site_user")
        env.setdefault("DB_PASSWORD", "StrongPass123!")
        env.setdefault("DB_HOST", "db")
        env.setdefault("DB_PORT", "5432")
        env.setdefault("SECRET_KEY", "test-secret-key")
        env.setdefault("DEBUG", "False")
        env.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1")
        env.setdefault("REDIS_URL", "redis://redis:6379/1")
        env.setdefault("CELERY_BROKER_URL", "redis://redis:6379/2")
        env.setdefault("CELERY_RESULT_BACKEND", "redis://redis:6379/3")
        env.setdefault("ELASTICSEARCH_URL", "http://elasticsearch:9200")
        env.setdefault("SENTRY_DSN", "")
        env.setdefault("SENTRY_TRACES_SAMPLE_RATE", "0")
        env.setdefault("SENTRY_PROFILES_SAMPLE_RATE", "0")

        result = subprocess.run(
            [docker, "compose", "-f", "docker-compose.prod.yml", "config"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("services:", result.stdout)
