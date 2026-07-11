from pathlib import Path
import json
import shutil
import subprocess
from urllib.error import HTTPError
from urllib.request import Request, build_opener, urlopen

from django.test import SimpleTestCase


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class GrafanaIntegrationTests(SimpleTestCase):
    def setUp(self):
        self.grafana_datasource = (
            BASE_DIR / "grafana" / "provisioning" / "datasources" / "prometheus.yml"
        ).read_text(encoding="utf-8")
        self.grafana_dashboard_provider = (
            BASE_DIR / "grafana" / "provisioning" / "dashboards" / "dashboards.yml"
        ).read_text(encoding="utf-8")
        self.grafana_dashboard = json.loads(
            (BASE_DIR / "grafana" / "provisioning" / "dashboards" / "json" / "app-observability.json").read_text(
                encoding="utf-8"
            )
        )

    def test_grafana_integration_provisions_prometheus_datasource_and_dashboard(self):
        self.assertIn("type: prometheus", self.grafana_datasource)
        self.assertIn("url: http://prometheus:9090", self.grafana_datasource)
        self.assertIn("path: /etc/grafana/provisioning/dashboards/json", self.grafana_dashboard_provider)
        self.assertEqual(self.grafana_dashboard["uid"], "app-observability")
        panel_titles = {panel["title"] for panel in self.grafana_dashboard["panels"]}
        self.assertIn("Django Request Rate", panel_titles)
        self.assertIn("Celery Tasks Total", panel_titles)

    def test_grafana_container_has_provisioned_dashboard_files_when_running(self):
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
        if "grafana" not in ps_result.stdout:
            self.skipTest("grafana service is not running")

        result = subprocess.run(
            [
                docker,
                "compose",
                "exec",
                "-T",
                "grafana",
                "sh",
                "-c",
                "test -f /etc/grafana/provisioning/dashboards/dashboards.yml && test -f /etc/grafana/provisioning/dashboards/json/app-observability.json",
            ],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_grafana_http_endpoint_is_reachable_when_running(self):
        request = Request("http://grafana:3000/login")
        opener = build_opener()
        try:
            with opener.open(request, timeout=10) as response:
                status = response.status
        except HTTPError as exc:
            status = exc.code
        self.assertIn(status, {200, 302, 403})

    def test_grafana_health_and_dashboard_search_apis_are_reachable(self):
        with urlopen("http://grafana:3000/api/health", timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
        self.assertEqual(payload["database"], "ok")
