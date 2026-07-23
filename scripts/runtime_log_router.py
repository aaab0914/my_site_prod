import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from my_site.logging_policy import RUNTIME_LOG_TARGETS, runtime_log_path


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: runtime_log_router.py <log-key>")

    target_key = sys.argv[1]
    target_map = {target.key: target for target in RUNTIME_LOG_TARGETS}
    target = target_map.get(target_key)
    if target is None:
        raise SystemExit(f"unknown log key: {target_key}")

    while True:
        line = sys.stdin.readline()
        if not line:
            break
        path = runtime_log_path("/code/logs", target)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", errors="replace") as handle:
            handle.write(line)
        sys.stdout.write(line)
        sys.stdout.flush()


if __name__ == "__main__":
    main()
