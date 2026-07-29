import os
from pathlib import Path
import shutil
import subprocess
import unittest


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class ProdStackSimulationTests(unittest.TestCase):
    def setUp(self):
        self.compose = (BASE_DIR / "docker-compose.prod.yml").read_text(encoding="utf-8")
        self.dockerfile = (BASE_DIR / "Dockerfile.prod").read_text(encoding="utf-8")
        self.entrypoint = (BASE_DIR / "entrypoint.sh").read_text(encoding="utf-8")
        self.nginx = (BASE_DIR / "nginx.prod.conf").read_text(encoding="utf-8")

    def test_prod_compose_config_is_valid_with_simulated_env(self):
        docker = shutil.which("docker")
        if docker is None:
            self.skipTest("docker is not installed in this environment")

        env = os.environ.copy()
        env.update(
            {
                "DB_NAME": "my_site_db",
                "DB_USER": "my_site_user",
                "DB_PASSWORD": "StrongPass123!",
                "DB_HOST": "db",
                "DB_PORT": "5432",
                "SECRET_KEY": "test-secret-key-not-for-production",
                "DEBUG": "False",
                "ALLOWED_HOSTS": "localhost,127.0.0.1",
                "CSRF_TRUSTED_ORIGINS": "https://localhost",
                "REDIS_URL": "redis://redis:6379/0",
                "CELERY_BROKER_URL": "redis://redis:6379/0",
                "CELERY_RESULT_BACKEND": "redis://redis:6379/0",
                "ELASTICSEARCH_URL": "http://elasticsearch:9200",
                "SENTRY_DSN": "",
                "SENTRY_TRACES_SAMPLE_RATE": "0",
                "SENTRY_PROFILES_SAMPLE_RATE": "0",
                "RUNNING_IN_DOCKER": "true",
            }
        )

        result = subprocess.run(
            [docker, "compose", "-f", "docker-compose.prod.yml", "--profile", "optional", "config"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("services:", result.stdout)
        for service in ["web", "nginx", "celery", "celery-beat", "db", "redis"]:
            with self.subTest(service=service):
                self.assertIn(f"{service}:", result.stdout)

    def test_prod_dockerfile_and_entrypoint_use_gunicorn_not_runserver(self):
        self.assertIn("DJANGO_SETTINGS_MODULE=my_site.settings.prod", self.dockerfile)
        self.assertIn("COPY entrypoint.sh /usr/local/bin/entrypoint.sh", self.dockerfile)
        self.assertIn('ENTRYPOINT ["sh", "/usr/local/bin/entrypoint.sh"]', self.dockerfile)
        self.assertIn("python /code/validate_prod_env.py", self.entrypoint)
        self.assertIn("python manage.py check --deploy", self.entrypoint)
        self.assertIn("python manage.py collectstatic --noinput", self.entrypoint)
        self.assertIn("exec gosu app gunicorn", self.entrypoint)
        self.assertIn("--bind 0.0.0.0:8000", self.entrypoint)
        self.assertNotIn("runserver", self.entrypoint)

    def test_prod_nginx_routes_static_media_and_django_upstream(self):
        self.assertIn("listen 80;", self.nginx)
        self.assertIn("listen 443 ssl;", self.nginx)
        self.assertIn("set $django_upstream http://web:8000;", self.nginx)
        self.assertIn("location /static/", self.nginx)
        self.assertIn("alias /static/;", self.nginx)
        self.assertIn("location /media/", self.nginx)
        self.assertIn("proxy_pass $django_upstream;", self.nginx)
        self.assertIn("proxy_set_header X-Forwarded-Proto https;", self.nginx)


if __name__ == "__main__":
    unittest.main()
