import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path
from textwrap import dedent

from django.test import SimpleTestCase


BASE_DIR = Path(__file__).resolve().parent.parent.parent
SH_BIN = shutil.which("sh")


class ShellScriptTestCase(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not SH_BIN:
            raise unittest.SkipTest("POSIX sh is required to execute shell-script tests")

    def make_executable(self, path: Path) -> None:
        path.chmod(path.stat().st_mode | stat.S_IEXEC)

    def write_file(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
        self.make_executable(path)

    def run_script(self, script_path: Path, env: dict[str, str] | None = None, args: list[str] | None = None):
        command = [SH_BIN, str(script_path)]
        if args:
            command.extend(args)
        return subprocess.run(
            command,
            cwd=script_path.parent,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )


class BackupDbScriptTests(ShellScriptTestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="backup-db-script-"))
        self.script_path = self.temp_dir / "backup_db.sh"
        shutil.copyfile(BASE_DIR / "backup_db.sh", self.script_path)
        self.make_executable(self.script_path)
        (self.temp_dir / "docker-compose.prod.yml").write_text("services: {}\n", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_fake_runtime(self, docker_name: str, dump_output: str = "fake-sql;\n", exit_code: int = 0):
        bin_dir = self.temp_dir / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        log_file = self.temp_dir / "docker-invocations.log"
        docker_script = dedent(
            f"""\
            #!/bin/sh
            printf '%s\\n' "$0 $*" >> "{log_file.as_posix()}"
            if [ "{exit_code}" -eq 0 ]; then
              printf '%s' '{dump_output}'
              exit 0
            fi
            exit {exit_code}
            """
        )
        self.write_file(bin_dir / docker_name, docker_script)
        return bin_dir, log_file

    def test_linux_mode_uses_docker_binary_and_writes_backup(self):
        bin_dir, log_file = self.create_fake_runtime("docker")
        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"

        result = self.run_script(self.script_path, env=env)

        self.assertEqual(result.returncode, 0, result.stderr)
        backups = list((self.temp_dir / "backups" / "db").glob("my_site_db_*.sql"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_text(encoding="utf-8"), "fake-sql;\n")
        log_text = (self.temp_dir / "logs" / "backup.log").read_text(encoding="utf-8")
        self.assertIn("Starting database backup", log_text)
        self.assertIn("Backup succeeded", log_text)
        self.assertIn("docker compose -f", log_file.read_text(encoding="utf-8"))

    def test_windows_mode_falls_back_to_docker_exe(self):
        bin_dir, log_file = self.create_fake_runtime("docker.exe", dump_output="windows-sql;\n")
        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"

        result = self.run_script(self.script_path, env=env)

        self.assertEqual(result.returncode, 0, result.stderr)
        backups = list((self.temp_dir / "backups" / "db").glob("my_site_db_*.sql"))
        self.assertEqual(backups[0].read_text(encoding="utf-8"), "windows-sql;\n")
        invocation = log_file.read_text(encoding="utf-8")
        self.assertIn("docker.exe compose -f", invocation)

    def test_macos_mode_keeps_only_latest_seven_backups(self):
        bin_dir, _ = self.create_fake_runtime("docker", dump_output="macos-sql;\n")
        backup_dir = self.temp_dir / "backups" / "db"
        backup_dir.mkdir(parents=True, exist_ok=True)
        for index in range(1, 9):
            (backup_dir / f"my_site_db_2026010{index}_000000.sql").write_text(str(index), encoding="utf-8")

        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"

        result = self.run_script(self.script_path, env=env)

        self.assertEqual(result.returncode, 0, result.stderr)
        sql_files = sorted(backup_dir.glob("*.sql"))
        self.assertEqual(len(sql_files), 7)

    def test_missing_docker_fails_cleanly(self):
        env = os.environ.copy()
        env["PATH"] = os.pathsep.join(["/bin", "/usr/bin"])

        result = self.run_script(self.script_path, env=env)

        self.assertEqual(result.returncode, 1)
        log_text = (self.temp_dir / "logs" / "backup.log").read_text(encoding="utf-8")
        self.assertIn("docker command not found", log_text)


class EntrypointScriptTests(ShellScriptTestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="entrypoint-script-"))
        self.code_dir = self.temp_dir / "code"
        self.code_dir.mkdir(parents=True, exist_ok=True)
        self.script_path = self.code_dir / "entrypoint.sh"
        script_text = (BASE_DIR / "entrypoint.sh").read_text(encoding="utf-8")
        script_text = script_text.replace("/code", self.code_dir.as_posix())
        self.script_path.write_text(script_text, encoding="utf-8", newline="\n")
        self.make_executable(self.script_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_fake_bin(self):
        bin_dir = self.temp_dir / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        call_log = self.temp_dir / "call-log.txt"

        self.write_file(
            bin_dir / "chown",
            dedent(
                f"""\
                #!/bin/sh
                printf 'chown %s\\n' "$*" >> "{call_log.as_posix()}"
                exit 0
                """
            ),
        )
        self.write_file(
            bin_dir / "chmod",
            dedent(
                f"""\
                #!/bin/sh
                printf 'chmod %s\\n' "$*" >> "{call_log.as_posix()}"
                exit 0
                """
            ),
        )
        self.write_file(
            bin_dir / "date",
            dedent(
                """\
                #!/bin/sh
                if [ "$1" = "+%Y-%m" ]; then
                  printf '2026-07'
                  exit 0
                fi
                if [ "$1" = "+%Y-%m-%d" ]; then
                  printf '2026-07-13'
                  exit 0
                fi
                /bin/date "$@"
                """
            ),
        )
        self.write_file(
            bin_dir / "python",
            dedent(
                f"""\
                #!/bin/sh
                printf 'python %s\\n' "$*" >> "{call_log.as_posix()}"
                exit 0
                """
            ),
        )
        self.write_file(
            bin_dir / "gunicorn",
            dedent(
                f"""\
                #!/bin/sh
                printf 'gunicorn %s\\n' "$*" >> "{call_log.as_posix()}"
                exit 0
                """
            ),
        )
        return bin_dir, call_log

    def build_env(self, bin_dir: Path, settings_module: str) -> dict[str, str]:
        env = os.environ.copy()
        env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"
        env["DJANGO_SETTINGS_MODULE"] = settings_module
        return env

    def test_linux_dev_mode_runs_manage_checks_and_gunicorn(self):
        bin_dir, call_log = self.create_fake_bin()
        env = self.build_env(bin_dir, "my_site.settings.dev")

        result = self.run_script(self.script_path, env=env)

        self.assertEqual(result.returncode, 0, result.stderr)
        log_text = call_log.read_text(encoding="utf-8")
        self.assertIn("python manage.py check", log_text)
        self.assertIn("python manage.py collectstatic --noinput", log_text)
        self.assertNotIn("validate_prod_env.py", log_text)
        self.assertIn("gunicorn --workers 2 --bind 0.0.0.0:8000", log_text)
        self.assertTrue((self.code_dir / "logs" / "2026-07").exists())

    def test_macos_prod_mode_runs_prod_validation_before_start(self):
        bin_dir, call_log = self.create_fake_bin()
        env = self.build_env(bin_dir, "my_site.settings.prod")

        result = self.run_script(self.script_path, env=env)

        self.assertEqual(result.returncode, 0, result.stderr)
        log_text = call_log.read_text(encoding="utf-8")
        self.assertIn(f"python {self.code_dir.as_posix()}/validate_prod_env.py", log_text)
        self.assertIn("python manage.py check --deploy", log_text)
        self.assertIn("python manage.py check", log_text)

    def test_windows_mode_executes_passed_command_instead_of_gunicorn(self):
        bin_dir, call_log = self.create_fake_bin()
        self.write_file(
            bin_dir / "echo",
            dedent(
                f"""\
                #!/bin/sh
                printf 'echo %s\\n' "$*" >> "{call_log.as_posix()}"
                exit 0
                """
            ),
        )
        env = self.build_env(bin_dir, "my_site.settings.dev")

        result = self.run_script(self.script_path, env=env, args=["echo", "hello-from-windows"])

        self.assertEqual(result.returncode, 0, result.stderr)
        log_text = call_log.read_text(encoding="utf-8")
        self.assertIn("echo hello-from-windows", log_text)
        self.assertNotIn("gunicorn --workers 2", log_text)
