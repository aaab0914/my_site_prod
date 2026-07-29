import os
from pathlib import Path
import shutil
import subprocess
import unittest


BASE_DIR = Path(__file__).resolve().parent.parent.parent
COMPOSE_FILE = BASE_DIR / "docker-compose.dev.yml"
ENV_FILE = BASE_DIR / ".env.dev"


class DevComposeFileExistenceTests(unittest.TestCase):
    """验证 dev compose 文件存在且非空"""

    def test_compose_dev_file_exists(self):
        self.assertTrue(COMPOSE_FILE.exists(), "docker-compose.dev.yml 不存在")

    def test_compose_dev_file_not_empty(self):
        self.assertGreater(COMPOSE_FILE.stat().st_size, 0, "docker-compose.dev.yml 是空文件")


class DevComposeServiceStructureTests(unittest.TestCase):
    """验证 dev compose 定义了核心服务"""

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

    def test_does_not_have_nginx(self):
        self.assertNotIn("nginx:", self.text)


class DevComposeWebServiceConfigTests(unittest.TestCase):
    """验证 web 服务的关键配置"""

    def setUp(self):
        self.text = COMPOSE_FILE.read_text(encoding="utf-8")

    def test_uses_dockerfile_dev(self):
        self.assertIn("dockerfile: Dockerfile.dev", self.text)

    def test_env_file_references_dev(self):
        """环境和 Django 配置通过 .env.dev 注入（而非写在 compose 里）"""
        self.assertIn("env_file:\n      - .env.dev", self.text)

    def test_uses_runserver_command(self):
        self.assertIn("runserver 0.0.0.0:8000", self.text)

    def test_mounts_project_code(self):
        self.assertIn("- .:/code", self.text)

    def test_mounts_static_media_logs_backups(self):
        self.assertIn("./staticfiles:/code/staticfiles", self.text)
        self.assertIn("./media:/code/media", self.text)
        self.assertIn("./logs:/code/logs", self.text)
        self.assertIn("./backups:/code/backups", self.text)

    def test_exposes_port_8000(self):
        self.assertIn('${DEV_WEB_PORT:-8001}:8000', self.text)

    def test_db_depends_on_healthcheck(self):
        self.assertIn("db:", self.text)
        self.assertIn("condition: service_healthy", self.text)


class DevEnvFileTests(unittest.TestCase):
    """验证 .env.dev 文件包含必要的环境变量（原 compose environment 中的变量已移入此处）"""

    def test_env_file_has_django_settings(self):
        text = ENV_FILE.read_text(encoding="utf-8")
        self.assertIn("DJANGO_SETTINGS_MODULE=my_site.settings.dev", text)

    def test_env_file_has_db_vars(self):
        text = ENV_FILE.read_text(encoding="utf-8")
        self.assertIn("DB_NAME=", text)
        self.assertIn("DB_USER=", text)
        self.assertIn("DB_PASSWORD=", text)
        self.assertIn("DB_HOST=", text)
        self.assertIn("DB_PORT=", text)

    def test_env_file_has_redis_url(self):
        text = ENV_FILE.read_text(encoding="utf-8")
        self.assertIn("REDIS_URL=", text)

    def test_env_file_has_celery_vars(self):
        text = ENV_FILE.read_text(encoding="utf-8")
        self.assertIn("CELERY_BROKER_URL=", text)
        self.assertIn("CELERY_RESULT_BACKEND=", text)
        self.assertIn("CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP=", text)

    def test_env_file_has_dev_host_port_vars(self):
        text = ENV_FILE.read_text(encoding="utf-8")
        self.assertIn("DEV_DB_PORT=", text)
        self.assertIn("DEV_WEB_PORT=", text)

    def test_env_file_has_database_url(self):
        text = ENV_FILE.read_text(encoding="utf-8")
        self.assertIn("DATABASE_URL=postgresql://", text)


class DevComposeDatabaseConfigTests(unittest.TestCase):
    """验证 PostgreSQL 配置"""

    def setUp(self):
        self.text = COMPOSE_FILE.read_text(encoding="utf-8")

    def test_db_service_uses_postgres_16(self):
        self.assertIn("image: postgres:16", self.text)

    def test_db_service_has_healthcheck(self):
        self.assertIn("healthcheck:", self.text)
        self.assertIn("pg_isready -U $$DB_USER -d $$DB_NAME", self.text)

    def test_db_service_exposes_port_5432(self):
        self.assertIn('${DEV_DB_PORT:-5433}:5432', self.text)


class DevComposeRedisConfigTests(unittest.TestCase):
    """验证 Redis 配置"""

    def setUp(self):
        self.text = COMPOSE_FILE.read_text(encoding="utf-8")

    def test_redis_uses_redis_7(self):
        self.assertIn("image: redis:7", self.text)

    def test_redis_has_healthcheck(self):
        self.assertIn('test: ["CMD", "redis-cli", "ping"]', self.text)


class DevComposeElasticsearchConfigTests(unittest.TestCase):
    """验证 Elasticsearch 配置"""

    def setUp(self):
        self.text = COMPOSE_FILE.read_text(encoding="utf-8")

    def test_elasticsearch_uses_correct_image(self):
        self.assertIn("docker.elastic.co/elasticsearch/elasticsearch:8.14.3", self.text)

    def test_elasticsearch_single_node(self):
        self.assertIn("discovery.type: single-node", self.text)

    def test_elasticsearch_disables_security(self):
        self.assertIn('xpack.security.enabled: "false"', self.text)

    def test_elasticsearch_limits_memory(self):
        self.assertIn("-Xms192m -Xmx192m", self.text)

    def test_elasticsearch_has_named_volume(self):
        self.assertIn("elasticsearch_data:", self.text)


class DevComposeCeleryConfigTests(unittest.TestCase):
    """验证 Celery worker/beat 配置"""

    def setUp(self):
        self.text = COMPOSE_FILE.read_text(encoding="utf-8")

    def test_celery_worker_command(self):
        self.assertIn("celery -A my_site worker", self.text)

    def test_celery_beat_command(self):
        self.assertIn("celery -A my_site beat", self.text)

    def test_celery_services_use_dev_dockerfile(self):
        # Count occurrences
        count = self.text.count("dockerfile: Dockerfile.dev")
        self.assertGreaterEqual(count, 3)  # web + celery + celery-beat


class DevComposeVolumeTests(unittest.TestCase):
    """验证命名卷声明"""

    def setUp(self):
        self.text = COMPOSE_FILE.read_text(encoding="utf-8")

    def test_has_postgres_named_volume(self):
        self.assertIn("postgres_data:", self.text)

    def test_has_elasticsearch_named_volume(self):
        self.assertIn("elasticsearch_data:", self.text)


@unittest.skipIf(shutil.which("docker") is None, "Docker 未安装，跳过")
class DevComposeConfigValidationTests(unittest.TestCase):
    """当 Docker 可用时验证 compose 配置合法性"""

    @classmethod
    def setUpClass(cls):
        cls.env = os.environ.copy()
        cls.env.update({
            "DB_NAME": "test_db",
            "DB_USER": "test_user",
            "DB_PASSWORD": "TestPass123!",
            "DB_HOST": "db",
            "DB_PORT": "5432",
            "SECRET_KEY": "test-secret-key-not-for-production",
            "DEBUG": "True",
            "ALLOWED_HOSTS": "localhost,127.0.0.1",
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
        for svc in ["db", "web", "redis", "elasticsearch", "celery", "celery-beat"]:
            with self.subTest(service=svc):
                self.assertIn(svc, services)


if __name__ == "__main__":
    unittest.main()
