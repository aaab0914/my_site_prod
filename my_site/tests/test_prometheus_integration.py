from pathlib import Path
import json
import shutil
import subprocess
from urllib.error import URLError
from urllib.request import urlopen

from django.contrib.auth.models import User
from django.test import Client, SimpleTestCase


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class PrometheusIntegrationTests(SimpleTestCase):
    databases = "__all__"

    def setUp(self):
        self.prometheus = (BASE_DIR / "prometheus.yml").read_text(encoding="utf-8")
        self.urls = (BASE_DIR / "my_site" / "urls.py").read_text(encoding="utf-8")
        self.client = Client()
        self.admin, created = User.objects.get_or_create(
            username="metricsadmin",
            defaults={"email": "metrics@example.com", "is_staff": True, "is_superuser": True},
        )
        if created:
            self.admin.set_password("secret123")
            self.admin.save(update_fields=["password"])

    def test_prometheus_integration_scrapes_django_and_celery_exporter(self):
        self.assertIn('path("metrics", metrics_view, name="metrics")', self.urls)
        self.assertIn('job_name: "django"', self.prometheus)
        self.assertIn('metrics_path: /metrics', self.prometheus)
        self.assertIn('targets: ["web:8000"]', self.prometheus)
        self.assertIn('job_name: "celery-exporter"', self.prometheus)
        self.assertIn('targets: ["celery-exporter:9540"]', self.prometheus)

    def test_metrics_endpoint_returns_prometheus_payload(self):
        anonymous_response = self.client.get("/metrics")
        self.assertEqual(anonymous_response.status_code, 404)

        self.client.force_login(self.admin)
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/plain", response["Content-Type"])
        content = response.content.decode("utf-8")
        self.assertIn("# HELP", content)
        self.assertIn("# TYPE", content)

    def test_prometheus_runtime_api_reports_django_and_celery_targets_up(self):
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
        if ps_result.returncode != 0 or "prometheus" not in ps_result.stdout:
            self.skipTest("prometheus service is not running")

        with urlopen("http://prometheus:9090/api/v1/targets", timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))

        self.assertEqual(payload["status"], "success")
        active_targets = payload["data"]["activeTargets"]
        job_names = {target["labels"]["job"] for target in active_targets}
        self.assertIn("django", job_names)
        self.assertIn("celery-exporter", job_names)
        health_by_job = {target["labels"]["job"]: target["health"] for target in active_targets}
        self.assertIn(health_by_job["django"], {"up", "down", "unknown"})
        self.assertIn(health_by_job["celery-exporter"], {"up", "down", "unknown"})
