from pathlib import Path
import shutil
import subprocess
import os

from django.test import SimpleTestCase


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class DockerComposeFileTests(SimpleTestCase):
    def setUp(self):
        self.compose_path = BASE_DIR / "docker-compose.yml"
        self.compose_text = self.compose_path.read_text(encoding="utf-8")
        self.prod_compose_path = BASE_DIR / "docker-compose.prod.yml"
        self.prod_compose_text = self.prod_compose_path.read_text(encoding="utf-8")
        self.readme_path = BASE_DIR / "README.md"
        self.readme_text = self.readme_path.read_text(encoding="utf-8")
        self.deploy_local_path = BASE_DIR / "deploy-local.sh"
        self.deploy_local_text = self.deploy_local_path.read_text(encoding="utf-8")
        self.deploy_prod_path = BASE_DIR / "deploy-prod.sh"
        self.deploy_prod_text = self.deploy_prod_path.read_text(encoding="utf-8")
        self.production_verification_path = BASE_DIR / "PRODUCTION_VERIFICATION.md"
        self.production_verification_text = self.production_verification_path.read_text(encoding="utf-8")

    def test_compose_file_exists(self):
        self.assertTrue(self.compose_path.exists())

    def test_production_compose_file_exists(self):
        self.assertTrue(self.prod_compose_path.exists())

    def test_compose_defines_expected_services(self):
        self.assertIn("services:", self.compose_text)
        self.assertIn("db:", self.compose_text)
        self.assertIn("web:", self.compose_text)
        self.assertIn("nginx:", self.compose_text)

    def test_db_service_uses_postgres_16(self):
        self.assertIn("image: postgres:16", self.compose_text)

    def test_db_service_has_healthcheck(self):
        self.assertIn("healthcheck:", self.compose_text)
        self.assertIn("pg_isready -U ${DB_USER} -d ${DB_NAME}", self.compose_text)

    def test_db_service_uses_environment_substitution_for_secrets(self):
        self.assertIn("POSTGRES_DB: ${DB_NAME}", self.compose_text)
        self.assertIn("POSTGRES_USER: ${DB_USER}", self.compose_text)
        self.assertIn("POSTGRES_PASSWORD: ${DB_PASSWORD}", self.compose_text)

    def test_web_service_builds_from_current_directory(self):
        self.assertIn("build: .", self.compose_text)

    def test_web_service_uses_internal_database_host(self):
        self.assertIn("DB_HOST: ${DB_HOST}", self.compose_text)

    def test_web_service_uses_environment_substitution_for_database_settings(self):
        self.assertIn("DJANGO_SETTINGS_MODULE: my_site.settings.dev", self.compose_text)
        self.assertIn("DB_NAME: ${DB_NAME}", self.compose_text)
        self.assertIn("DB_USER: ${DB_USER}", self.compose_text)
        self.assertIn("DB_PASSWORD: ${DB_PASSWORD}", self.compose_text)
        self.assertIn("DB_PORT: ${DB_PORT}", self.compose_text)

    def test_web_service_mounts_project_code(self):
        self.assertIn("- .:/code", self.compose_text)

    def test_web_service_mounts_static_media_and_backups(self):
        self.assertIn("- ./staticfiles:/code/staticfiles", self.compose_text)
        self.assertIn("- ./media:/code/media", self.compose_text)
        self.assertIn("- ./backups:/code/backups", self.compose_text)

    def test_web_service_has_healthcheck(self):
        self.assertIn("healthcheck:", self.compose_text)
        self.assertIn("urllib.request.Request('http://127.0.0.1:8000/users/login/'", self.compose_text)
        self.assertIn("build_opener(NoRedirect)", self.compose_text)
        self.assertIn("'X-Forwarded-Proto': 'https'", self.compose_text)
        self.assertIn("start_period: 30s", self.compose_text)
        self.assertIn("timeout: 15s", self.compose_text)
        self.assertIn("retries: 8", self.compose_text)

    def test_nginx_service_mounts_expected_files(self):
        self.assertIn("- ./nginx.conf:/etc/nginx/conf.d/default.conf", self.compose_text)
        self.assertIn("- ./staticfiles:/static", self.compose_text)
        self.assertIn("- ./media:/media", self.compose_text)

    def test_nginx_waits_for_web_health(self):
        self.assertIn("condition: service_healthy", self.compose_text)

    def test_compose_declares_named_volumes(self):
        self.assertIn("volumes:", self.compose_text)
        self.assertIn("postgres_data:", self.compose_text)
        self.assertNotIn("backups_volume:", self.compose_text)

    def test_production_compose_does_not_bind_mount_project_code(self):
        self.assertNotIn("- .:/code", self.prod_compose_text)
        self.assertNotIn("/code:ro", self.prod_compose_text)

    def test_production_compose_uses_read_only_proxy_and_static_mounts(self):
        self.assertIn("./nginx.conf:/etc/nginx/conf.d/default.conf:ro", self.prod_compose_text)
        self.assertIn("./staticfiles:/static:ro", self.prod_compose_text)
        self.assertIn("./media:/media:ro", self.prod_compose_text)
        self.assertIn("DJANGO_SETTINGS_MODULE: my_site.settings.prod", self.prod_compose_text)

    def test_production_deploy_script_exists(self):
        self.assertTrue(self.deploy_prod_path.exists())

    def test_production_deploy_script_targets_prod_compose(self):
        self.assertIn('COMPOSE_FILE="docker-compose.prod.yml"', self.deploy_prod_text)
        self.assertIn('docker compose -f "${COMPOSE_FILE}" up -d --build', self.deploy_prod_text)
        self.assertIn('docker compose -f "${COMPOSE_FILE}" exec -T web python manage.py check --deploy', self.deploy_prod_text)
        self.assertIn('docker compose -f "${COMPOSE_FILE}" exec -T web python manage.py migrate', self.deploy_prod_text)
        self.assertIn('docker compose -f "${COMPOSE_FILE}" exec -T db pg_isready', self.deploy_prod_text)
        self.assertIn('curl -fsSI "${APP_BASE_URL}/users/login/"', self.deploy_prod_text)
        self.assertIn('curl -fsSI "${APP_BASE_URL}/blog/create/"', self.deploy_prod_text)
        self.assertIn('trap print_logs_on_failure ERR', self.deploy_prod_text)

    def test_local_deploy_script_stays_dev_only(self):
        self.assertIn("local development deployment", self.deploy_local_text)
        self.assertNotIn("docker-compose.prod.yml", self.deploy_local_text)

    def test_readme_explicitly_requires_prod_compose_for_server_deploys(self):
        self.assertIn("Server production deployment must use `docker-compose.prod.yml`.", self.readme_text)
        self.assertIn("Do not use plain `docker compose up` for production", self.readme_text)
        self.assertIn("bash ./deploy-prod.sh", self.readme_text)

    def test_production_verification_checklist_exists(self):
        self.assertTrue(self.production_verification_path.exists())

    def test_production_verification_checklist_targets_prod_compose(self):
        self.assertIn("docker-compose.prod.yml", self.production_verification_text)
        self.assertIn("Do not use plain `docker compose up` on the server.", self.production_verification_text)
        self.assertIn("curl http://localhost/blog/", self.production_verification_text)
        self.assertIn("curl -I http://localhost/blog/create/", self.production_verification_text)
        self.assertIn("docker compose -f docker-compose.prod.yml exec web python manage.py check --deploy", self.production_verification_text)

    def test_compose_config_is_valid_when_docker_is_available(self):
        docker = shutil.which("docker")
        if docker is None:
            self.skipTest("docker is not installed in this environment")

        result = subprocess.run(
            [docker, "compose", "config"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("services:", result.stdout)

    def test_compose_service_list_is_valid_when_docker_is_available(self):
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
