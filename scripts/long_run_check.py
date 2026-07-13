from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent.parent


def directory_summary(path: Path) -> dict[str, object]:
    total_size = 0
    file_count = 0
    latest_mtime = None
    if path.exists():
        for item in path.rglob("*"):
            if not item.is_file():
                continue
            stat = item.stat()
            total_size += stat.st_size
            file_count += 1
            modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
            if latest_mtime is None or modified > latest_mtime:
                latest_mtime = modified
    return {
        "exists": path.exists(),
        "files": file_count,
        "bytes": total_size,
        "latest_mtime_utc": latest_mtime.isoformat() if latest_mtime else None,
    }


def stale_log_files(path: Path, days: int) -> list[str]:
    if not path.exists():
        return []
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
    stale = []
    for item in path.rglob("*.log"):
        modified = datetime.fromtimestamp(item.stat().st_mtime, tz=timezone.utc)
        if modified < cutoff:
            stale.append(str(item.relative_to(PROJECT_DIR)).replace("\\", "/"))
    return sorted(stale)


def main() -> int:
    retention_days = int(os.environ.get("LOG_RETENTION_DAYS", "30"))
    report = {
        "generated_at_utc": datetime.now(tz=timezone.utc).isoformat(),
        "logs": directory_summary(PROJECT_DIR / "logs"),
        "backups": directory_summary(PROJECT_DIR / "backups"),
        "media": directory_summary(PROJECT_DIR / "media"),
        "stale_logs_older_than_retention": stale_log_files(PROJECT_DIR / "logs", retention_days)[:20],
    }
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
