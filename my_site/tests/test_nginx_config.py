from pathlib import Path
import shutil
import subprocess

from django.test import SimpleTestCase


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class NginxConfigFileTests(SimpleTestCase):
    def setUp(self):
        self.nginx_path = BASE_DIR / "nginx.conf"
        self.nginx_text = self.nginx_path.read_text(encoding="utf-8")

    def test_nginx_config_file_exists(self):
        self.assertTrue(self.nginx_path.exists())

    def test_server_block_is_defined(self):
        self.assertIn("server {", self.nginx_text)
        self.assertIn("listen 80;", self.nginx_text)
        self.assertIn("server_name _;", self.nginx_text)

    def test_client_upload_limit_is_defined(self):
        self.assertIn("client_max_body_size 25m;", self.nginx_text)

    def test_static_location_is_configured(self):
        self.assertIn("location /static/", self.nginx_text)
        self.assertIn("alias /static/;", self.nginx_text)

    def test_media_location_is_configured(self):
        self.assertIn("location /media/", self.nginx_text)
        self.assertIn("alias /media/;", self.nginx_text)

    def test_root_location_proxies_to_web_container(self):
        self.assertIn("location / {", self.nginx_text)
        self.assertIn("proxy_pass http://web:8000;", self.nginx_text)

    def test_proxy_headers_are_forwarded(self):
        self.assertIn("proxy_set_header Host $host;", self.nginx_text)
        self.assertIn("proxy_set_header X-Real-IP $remote_addr;", self.nginx_text)
        self.assertIn("proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;", self.nginx_text)
        self.assertIn("proxy_set_header X-Forwarded-Proto $scheme;", self.nginx_text)

    def test_nginx_config_syntax_when_nginx_is_available(self):
        nginx = shutil.which("nginx")
        if nginx is None:
            self.skipTest("nginx is not installed in this environment")

        result = subprocess.run(
            [nginx, "-t", "-c", str(self.nginx_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        combined_output = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 0, msg=combined_output)
