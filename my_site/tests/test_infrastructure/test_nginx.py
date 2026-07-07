import shutil
import subprocess

from django.test import SimpleTestCase

from .common import BASE_DIR


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
        result = subprocess.run([nginx, "-t", "-c", str(BASE_DIR / "nginx.conf")], capture_output=True, text=True, timeout=30)
        combined_output = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 0, msg=combined_output)
