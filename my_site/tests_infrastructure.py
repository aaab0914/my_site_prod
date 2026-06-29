from pathlib import Path
import shutil
import subprocess
from urllib.request import urlopen
from urllib.error import URLError

from django.test import SimpleTestCase


BASE_DIR = Path(__file__).resolve().parent.parent


class NginxConfigTests(SimpleTestCase):
    def setUp(self):
        self.nginx_conf = (BASE_DIR / "nginx.conf").read_text(encoding="utf-8")

    def test_nginx_proxies_to_web_container(self):
        self.assertIn("proxy_pass http://web:8000;", self.nginx_conf)

    def test_nginx_serves_static_and_media(self):
        self.assertIn("location /static/", self.nginx_conf)
        self.assertIn("alias /static/;", self.nginx_conf)
        self.assertIn("location /media/", self.nginx_conf)
        self.assertIn("alias /media/;", self.nginx_conf)

    def test_nginx_forwards_proxy_headers(self):
        self.assertIn("proxy_set_header Host $host;", self.nginx_conf)
        self.assertIn("proxy_set_header X-Forwarded-Proto $scheme;", self.nginx_conf)

    def test_nginx_config_passes_syntax_check_when_nginx_is_installed(self):
        nginx = shutil.which("nginx")
        if nginx is None:
            self.skipTest("nginx is not installed in this environment")

        result = subprocess.run(
            [nginx, "-t", "-c", str(BASE_DIR / "nginx.conf")],
            capture_output=True,
            text=True,
            timeout=30,
        )
        combined_output = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 0, msg=combined_output)


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
        self.assertIn("--workers 3", self.entrypoint)
        self.assertIn("--bind 0.0.0.0:8000", self.entrypoint)

    def test_gunicorn_configuration_is_valid_when_gunicorn_is_installed(self):
        gunicorn = shutil.which("gunicorn")
        if gunicorn is None:
            self.skipTest("gunicorn is not installed in this environment")

        result = subprocess.run(
            [
                gunicorn,
                "--check-config",
                "--workers",
                "3",
                "--bind",
                "0.0.0.0:8000",
                "my_site.wsgi:application",
            ],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)


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
        self.assertIn('python /code/validate_prod_env.py', self.entrypoint)


class ProductionValidationScriptTests(SimpleTestCase):
    def setUp(self):
        self.validator = (BASE_DIR / "validate_prod_env.py").read_text(encoding="utf-8")
        self.restore_script = (BASE_DIR / "restore_test.ps1").read_text(encoding="utf-8")

    def test_prod_env_validator_exists_and_checks_core_settings(self):
        self.assertIn('fail("Production environment must not run with DEBUG=True.")', self.validator)
        self.assertIn('ALLOWED_HOSTS must not be empty.', self.validator)
        self.assertIn("CSRF_TRUSTED_ORIGINS must not be empty in production.", self.validator)
        self.assertIn('SECURE_HSTS_SECONDS must be at least 31536000 in production.', self.validator)
        self.assertIn("DB_PASSWORD is too weak or still uses a placeholder value.", self.validator)

    def test_restore_drill_script_exists_and_uses_latest_backup(self):
        self.assertIn('Sort-Object LastWriteTime -Descending', self.restore_script)
        self.assertIn('$DrillDbName = "my_site_restore_drill"', self.restore_script)
        self.assertIn('dropdb -U `"$POSTGRES_USER`" --if-exists $DrillDbName', self.restore_script)
        self.assertIn('createdb -U `"$POSTGRES_USER`" $DrillDbName', self.restore_script)


class MonitoringAndWorkflowTests(SimpleTestCase):
    def test_monitor_health_script_checks_blog_and_login_routes(self):
        monitor_script = (BASE_DIR / "monitor_health.py").read_text(encoding="utf-8")
        self.assertIn('/blog/', monitor_script)
        self.assertIn('/users/login/', monitor_script)
        self.assertIn('ALERT', monitor_script)

    def test_ci_workflow_runs_dependency_audit_and_image_scan(self):
        workflow = (BASE_DIR / ".github" / "workflows" / "docker-ci.yml").read_text(encoding="utf-8")
        self.assertIn("pip install pip-audit", workflow)
        self.assertIn("pip-audit -r requirements.txt", workflow)
        self.assertIn("aquasecurity/trivy-action", workflow)


class DockerRuntimeProbeTests(SimpleTestCase):
    def test_docker_binary_is_available_when_runtime_checks_are_requested(self):
        if shutil.which("docker") is None:
            self.skipTest("docker is not installed in this environment")

    def test_docker_compose_config_command_succeeds_when_docker_is_available(self):
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

        result = subprocess.run(
            [psql, "--version"],
            capture_output=True,
            text=True,
            timeout=15,
        )
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
            [
                docker,
                "compose",
                "exec",
                "-T",
                "db",
                "pg_isready",
                "-U",
                "my_site_user",
                "-d",
                "my_site_db",
            ],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        combined_output = f"{result.stdout}\n{result.stderr}".lower()
        self.assertEqual(result.returncode, 0, msg=combined_output)
        self.assertIn("accepting connections", combined_output)
