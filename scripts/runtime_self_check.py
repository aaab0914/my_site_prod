from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent
COMPOSE_FILE = PROJECT_DIR / "docker-compose.yml"
PROD_COMPOSE_FILE = PROJECT_DIR / "docker-compose.prod.yml"


def run_command(command: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(
        command,
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    return result.returncode, (result.stdout or "").strip(), (result.stderr or "").strip()


def check_compose(docker_bin: str, compose_file: Path) -> dict[str, object]:
    code, stdout, stderr = run_command([docker_bin, "compose", "-f", str(compose_file), "config"])
    return {
        "compose_file": compose_file.name,
        "ok": code == 0,
        "stderr": stderr,
        "contains_services": "services:" in stdout,
    }


def check_containers(docker_bin: str) -> dict[str, object]:
    code, stdout, stderr = run_command([docker_bin, "compose", "ps", "--format", "json"])
    if code != 0:
        return {"ok": False, "stderr": stderr, "services": []}

    services = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        services.append(
            {
                "service": item.get("Service"),
                "state": item.get("State"),
                "health": item.get("Health"),
            }
        )

    unhealthy = [service for service in services if service["state"] not in {"running"}]
    return {"ok": not unhealthy, "services": services, "stderr": stderr}


def main() -> int:
    docker_bin = shutil.which("docker") or shutil.which("docker.exe")
    if not docker_bin:
        print("docker command not found", file=sys.stderr)
        return 1

    results = {
        "local_compose": check_compose(docker_bin, COMPOSE_FILE),
        "prod_compose": check_compose(docker_bin, PROD_COMPOSE_FILE),
        "running_services": check_containers(docker_bin),
    }
    print(json.dumps(results, ensure_ascii=True, indent=2))
    return 0 if all(item["ok"] for item in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
