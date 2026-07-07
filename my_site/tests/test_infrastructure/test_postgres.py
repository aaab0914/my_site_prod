import shutil
import subprocess

from django.test import SimpleTestCase

from .common import BASE_DIR


class PostgresComposeConfigTests(SimpleTestCase):
    def setUp(self):
        self.compose = (BASE_DIR / "docker-compose.yml").read_text(encoding="utf-8")
        self.prod_compose = (BASE_DIR / "docker-compose.prod.yml").read_text(encoding="utf-8")

    def test_compose_declares_postgres_service(self):
        self.assertIn("db:", self.compose)
        self.assertIn("image: postgres:16", self.compose)

    def test_compose_sets_database_environment_with_env_substitution(self):
        self.assertIn("POSTGRES_DB: ${DB_NAME}", self.compose)
        self.assertIn("POSTGRES_USER: ${DB_USER}", self.compose)
        self.assertIn("POSTGRES_PASSWORD: ${DB_PASSWORD}", self.compose)

    def test_production_compose_sets_database_environment_with_env_substitution(self):
        self.assertIn("POSTGRES_DB: ${DB_NAME}", self.prod_compose)
        self.assertIn("POSTGRES_USER: ${DB_USER}", self.prod_compose)
        self.assertIn("POSTGRES_PASSWORD: ${DB_PASSWORD}", self.prod_compose)

    def test_compose_includes_postgres_healthcheck(self):
        self.assertIn("healthcheck:", self.compose)
        self.assertIn("pg_isready -U", self.compose)

    def test_web_uses_database_service_name(self):
        self.assertIn("DB_HOST: ${DB_HOST}", self.compose)
        self.assertIn("depends_on:", self.compose)
        self.assertIn("condition: service_healthy", self.compose)

    def test_compose_exposes_postgres_port_for_host_access(self):
        self.assertIn('- "5550:5432"', self.compose)


class PostgresRuntimeProbeTests(SimpleTestCase):
    def test_psql_binary_is_available_when_database_runtime_checks_are_requested(self):
        psql = shutil.which("psql")
        if psql is None:
            self.skipTest("psql is not installed in this environment")
        self.assertIsNotNone(psql)

    def test_psql_client_reports_version_when_installed(self):
        psql = shutil.which("psql")
        if psql is None:
            self.skipTest("psql is not installed in this environment")
        result = subprocess.run([psql, "--version"], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("psql", result.stdout.lower())

    def test_docker_compose_executes_pg_isready_when_containers_are_running(self):
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
        if "db" not in ps_result.stdout:
            self.skipTest("db service is not running")
        result = subprocess.run(
            [docker, "compose", "exec", "-T", "db", "pg_isready", "-U", "my_site_user", "-d", "my_site_db"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        combined_output = f"{result.stdout}\n{result.stderr}".lower()
        self.assertEqual(result.returncode, 0, msg=combined_output)
        self.assertIn("accepting connections", combined_output)
