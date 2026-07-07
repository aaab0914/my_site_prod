from django.test import SimpleTestCase

from .common import BASE_DIR


class ProductionValidationScriptTests(SimpleTestCase):
    def setUp(self):
        self.validator = (BASE_DIR / "validate_prod_env.py").read_text(encoding="utf-8")
        self.restore_script = (BASE_DIR / "restore_test.ps1").read_text(encoding="utf-8")

    def test_prod_env_validator_exists_and_checks_core_settings(self):
        self.assertIn('fail("Production environment must not run with DEBUG=True.")', self.validator)
        self.assertIn("ALLOWED_HOSTS must not be empty.", self.validator)
        self.assertIn("CSRF_TRUSTED_ORIGINS must not be empty in production.", self.validator)
        self.assertIn("SECURE_HSTS_SECONDS must be at least 31536000 in production.", self.validator)
        self.assertIn("DB_PASSWORD is too weak or still uses a placeholder value.", self.validator)

    def test_restore_drill_script_exists_and_uses_latest_backup(self):
        self.assertIn("Sort-Object LastWriteTime -Descending", self.restore_script)
        self.assertIn('$DrillDbName = "my_site_restore_drill"', self.restore_script)
        self.assertIn('dropdb -U `"$POSTGRES_USER`" --if-exists $DrillDbName', self.restore_script)
        self.assertIn('createdb -U `"$POSTGRES_USER`" $DrillDbName', self.restore_script)


class MonitoringAndWorkflowTests(SimpleTestCase):
    def test_monitor_health_script_checks_blog_and_login_routes(self):
        monitor_script = (BASE_DIR / "monitor_health.py").read_text(encoding="utf-8")
        self.assertIn("/blog/", monitor_script)
        self.assertIn("/users/login/", monitor_script)
        self.assertIn("ALERT", monitor_script)

    def test_ci_workflow_runs_dependency_audit_and_image_scan(self):
        workflow = (BASE_DIR / ".github" / "workflows" / "docker-ci.yml").read_text(encoding="utf-8")
        self.assertIn("pip install pip-audit", workflow)
        self.assertIn("pip-audit -r requirements.txt", workflow)
        self.assertIn("aquasecurity/trivy-action", workflow)
