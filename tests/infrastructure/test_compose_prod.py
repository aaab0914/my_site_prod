import os
from pathlib import Path
import shutil
import subprocess
import unittest


BASE_DIR = Path(__file__).resolve().parent.parent.parent
COMPOSE_FILE = BASE_DIR / "docker-compose.prod.yml"
ENV_FILE = BASE_DIR / ".env.prod"


class ProdComposeFileExistenceTests(unittest.TestCase):
    """验证 prod compose 文件存在且非空"""

    def test_compose_prod_file_exists(self):
        self.assertTrue(COMPOSE_FILE.exists(), "docker-compose.prod.yml 不存在")

    def test_compose_prod_file_not_empty(self):
        self.assertGreater(COMPOSE_FILE.stat().st_size, 0, "docker-compose.prod.yml 是空文件")


class ProdComposeServiceStructureTests(unittest.TestCase):
    """验证 prod compose 定义了核心服务"""

    def setUp(self):
        self.text = COMPOSE_FILE.read_text(encoding="utf-8")

    def test_defines_services_section(self):
        self.assertIn("services:", self.text)

    def test_defines_volumes_section(self):
        self.assertIn("volumes:", self.text)

    def test_has_db_service(self):
        self.assertIn("db:", self.text)

    def test_has_redis_service(self):
        self.assertIn("redis:", self.text)

    def test_has_elasticsearch_service(self):
        self.assertIn("elasticsearch:", self.text)

    def test_has_web_service(self):
        self.assertIn("web:", self.text)

    def test_has_celery_service(self):
        self.assertIn("celery:", self.text)

    def test_has_celery_beat_service(self):
        self.assertIn("celery-beat:", self.text)

    def test_has_flower_service(self):
        self.assertIn("flower:", self.text)

    def test_has_prometheus_service(self):
        self.assertIn("prometheus:", self.text)

    def test_has_grafana_service(self):
        self.assertIn("grafana:", self.text)

    def test_has_nginx_service(self):
        self.assertIn("nginx:", self.text)


class ProdComposeWebServiceConfigTests(unittest.TestCase):
    """验证 prod 版 web 服务的关键配置（与 dev 的核心区别）"""

    def setUp(self):
        self.text = COMPOSE_FILE.read_text(encoding="utf-8")

    def test_uses_dockerfile_prod(self):
        self.assertIn("dockerfile: Dockerfile.prod", self.text)

    def test_env_file_references_prod(self):
        self.assertIn("env_file:\n      - .env.prod", self.text)

    def test_does_not_bind_mount_project_code(self):
        """生产环境不应绑定挂载源码"""
        self.assertNotIn("- .:/code", self.text)
        self.assertNotIn("/code:ro", self.text)

    def test_mounts_static_media_logs_backups(self):
        self.assertIn("./staticfiles:/code/staticfiles", self.text)
        self.assertIn("./media:/code/media", self.text)
        self.assertIn("./logs:/code/logs", self.text)
        self.assertIn("./backups:/code/backups", self.text)

    def test_exposes_port_8000(self):
        self.assertIn('"8000:8000"', self.text)

    def test_db_depends_on_healthcheck(self):
        self.assertIn("condition: service_healthy", self.text)

    def test_web_service_has_healthcheck(self):
        self.assertIn("urllib.request.Request('http://127.0.0.1:8000/health/'", self.text)
        self.assertIn("exit(0 if r.status == 200 else 1)", self.text)

    def test_no_runserver_command(self):
        """生产环境不应使用 runserver"""
        self.assertNotIn("runserver", self.text)


class ProdComposeDatabaseConfigTests(unittest.TestCase):
    """验证 PostgreSQL 配置"""

    def setUp(self):
        self.text = COMPOSE_FILE.read_text(encoding="utf-8")

    def test_db_service_uses_postgres_16(self):
        self.assertIn("image: postgres:16", self.text)

    def test_db_service_has_healthcheck(self):
        self.assertIn("healthcheck:", self.text)
        self.assertIn("pg_isready -U ${DB_USER} -d ${DB_NAME}", self.text)

    def test_db_service_exposes_port_5433(self):
        """生产环境暴露 5433 避免与本地 PostgreSQL 冲突"""
        self.assertIn('"5433:5432"', self.text)


class ProdComposeRedisConfigTests(unittest.TestCase):
    """验证 Redis 配置"""

    def setUp(self):
        self.text = COMPOSE_FILE.read_text(encoding="utf-8")

    def test_redis_uses_redis_7(self):
        self.assertIn("image: redis:7", self.text)

    def test_redis_has_healthcheck(self):
        self.assertIn('test: ["CMD", "redis-cli", "ping"]', self.text)


class ProdComposeElasticsearchConfigTests(unittest.TestCase):
    """验证 Elasticsearch 配置"""

    def setUp(self):
        self.text = COMPOSE_FILE.read_text(encoding="utf-8")

    def test_elasticsearch_uses_correct_image(self):
        self.assertIn("docker.elastic.co/elasticsearch/elasticsearch:8.14.3", self.text)

    def test_elasticsearch_single_node(self):
        self.assertIn("discovery.type: single-node", self.text)

    def test_elasticsearch_limits_memory(self):
        self.assertIn("-Xms192m -Xmx192m", self.text)


class ProdComposeCeleryConfigTests(unittest.TestCase):
    """验证 Celery worker/beat/flower 配置"""

    def setUp(self):
        self.text = COMPOSE_FILE.read_text(encoding="utf-8")

    def test_celery_worker_command(self):
        self.assertIn("celery -A my_site worker", self.text)

    def test_celery_beat_command(self):
        self.assertIn("celery -A my_site beat", self.text)

    def test_celery_services_use_prod_dockerfile(self):
        count = self.text.count("dockerfile: Dockerfile.prod")
        self.assertGreaterEqual(count, 3)  # web + celery + celery-beat


class ProdComposeNginxConfigTests(unittest.TestCase):
    """验证 Nginx 配置"""

    def setUp(self):
        self.text = COMPOSE_FILE.read_text(encoding="utf-8")

    def test_nginx_is_optional_profile(self):
        self.assertIn("profiles: [\"optional\"]", self.text)

    def test_nginx_uses_nginx_125(self):
        self.assertIn("image: nginx:1.25", self.text)

    def test_nginx_mounts_conf_static_media_ssl(self):
        self.assertIn("./nginx.prod.conf:/etc/nginx/conf.d/default.conf:ro", self.text)
        self.assertIn("./staticfiles:/static:ro", self.text)
        self.assertIn("./media:/media:ro", self.text)
        self.assertIn("./ssl:/etc/nginx/ssl:ro", self.text)

    def test_nginx_exposes_80_and_443(self):
        self.assertIn('"8080:80"', self.text)
        self.assertIn('"8443:443"', self.text)

    def test_nginx_depends_on_web_healthy(self):
        self.assertIn("condition: service_healthy", self.text)


class ProdComposeOptionalServicesTests(unittest.TestCase):
    """验证可选服务（带 profile 标签）"""

    def setUp(self):
        self.text = COMPOSE_FILE.read_text(encoding="utf-8")

    def test_flower_has_optional_profile(self):
        self.assertIn("profiles: [\"optional\"]", self.text)

    def test_flower_binds_localhost_only(self):
        self.assertIn('"127.0.0.1:15556:5555"', self.text)

    def test_prometheus_has_optional_profile(self):
        self.assertIn("profiles: [\"optional\"]", self.text)

    def test_grafana_has_optional_profile(self):
        self.assertIn("profiles: [\"optional\"]", self.text)

    def test_loki_has_config_mount(self):
        self.assertIn("./loki/config.yml:/etc/loki/config.yml:ro", self.text)

    def test_promtail_reads_logs_dir(self):
        self.assertIn("./logs:/var/log/my_site:ro", self.text)


class ProdComposeVolumeTests(unittest.TestCase):
    """验证命名卷声明"""

    def setUp(self):
        self.text = COMPOSE_FILE.read_text(encoding="utf-8")

    def test_has_all_named_volumes(self):
        self.assertIn("postgres_data:", self.text)
        self.assertIn("elasticsearch_data:", self.text)
        self.assertIn("grafana_data:", self.text)
        self.assertIn("loki_data:", self.text)


@unittest.skipIf(shutil.which("docker") is None, "Docker 未安装，跳过")
class ProdComposeConfigValidationTests(unittest.TestCase):
    """当 Docker 可用时验证 compose 配置合法性"""

    @classmethod
    def setUpClass(cls):
        cls.env = os.environ.copy()
        cls.env.update({
            "DB_NAME": "test_db",
            "DB_USER": "test_user",
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
        })

    def test_compose_config_is_valid(self):
        result = subprocess.run(
            ["docker", "compose", "-f", str(COMPOSE_FILE), "config"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30,
            env={**self.env},
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("services:", result.stdout)

    def test_compose_service_list_contains_core_services(self):
        result = subprocess.run(
            ["docker", "compose", "-f", str(COMPOSE_FILE), "config", "--services"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=30,
            env={**self.env},
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        services = result.stdout.splitlines()
        # nginx 是 optional profile 服务，默认不显示，所以不在此处断言
        for svc in ["db", "web", "redis", "elasticsearch", "celery", "celery-beat"]:
            with self.subTest(service=svc):
                self.assertIn(svc, services)


class ProdEnvFileTests(unittest.TestCase):
    """验证 .env.prod 文件包含必要的环境变量"""

    def test_env_file_has_django_settings(self):
        text = ENV_FILE.read_text(encoding="utf-8")
        self.assertIn("DJANGO_SETTINGS_MODULE=my_site.settings.prod", text)

    def test_env_file_has_db_vars(self):
        text = ENV_FILE.read_text(encoding="utf-8")
        self.assertIn("DB_NAME=", text)
        self.assertIn("DB_USER=", text)
        self.assertIn("DB_PASSWORD=", text)
        self.assertIn("DB_HOST=db", text)
        self.assertIn("DB_PORT=5432", text)

    def test_env_file_has_database_url(self):
        text = ENV_FILE.read_text(encoding="utf-8")
        self.assertIn("DATABASE_URL=postgresql://", text)

    def test_env_file_has_security_vars(self):
        text = ENV_FILE.read_text(encoding="utf-8")
        self.assertIn("SECURE_SSL_REDIRECT=True", text)
        self.assertIn("SESSION_COOKIE_SECURE=True", text)
        self.assertIn("CSRF_COOKIE_SECURE=True", text)

    def test_env_file_has_debug_false(self):
        text = ENV_FILE.read_text(encoding="utf-8")
        self.assertIn("DEBUG=False", text)


if __name__ == "__main__":
    unittest.main()
