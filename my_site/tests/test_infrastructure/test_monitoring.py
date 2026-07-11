from django.test import SimpleTestCase

from .common import BASE_DIR


class ProductionValidationScriptTests(SimpleTestCase):
    def setUp(self):
        self.validator_path = BASE_DIR / "validate_prod_env.py"
        self.validator = self.validator_path.read_text(encoding="utf-8") if self.validator_path.exists() else ""
        self.restore_script_path = BASE_DIR / "restore_test.ps1"
        self.restore_script = self.restore_script_path.read_text(encoding="utf-8") if self.restore_script_path.exists() else ""

    def test_prod_env_validator_exists_and_checks_core_settings(self):
        self.assertIn('fail("Production environment must not run with DEBUG=True.")', self.validator)
        self.assertIn("ALLOWED_HOSTS must not be empty.", self.validator)
        self.assertIn("CSRF_TRUSTED_ORIGINS must not be empty in production.", self.validator)
        self.assertIn("SECURE_HSTS_SECONDS must be at least 31536000 in production.", self.validator)
        self.assertIn("DB_PASSWORD is too weak or still uses a placeholder value.", self.validator)

    def test_restore_drill_script_is_optional(self):
        self.assertFalse(self.restore_script_path.exists())


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
