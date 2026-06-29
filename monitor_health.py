from pathlib import Path
from datetime import datetime
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PROJECT_ROOT = Path(__file__).resolve().parent
MONTH_DIR = PROJECT_ROOT / "logs" / datetime.now().strftime("%Y-%m")
MONTH_DIR.mkdir(parents=True, exist_ok=True)
MONITOR_LOG = MONTH_DIR / "monitor-health.log"


def log(message: str) -> None:
    with MONITOR_LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"{message}\n")
    print(message)


def check_url(url: str, name: str) -> bool:
    try:
        response = urlopen(Request(url, headers={"User-Agent": "my-site-monitor/1.0"}), timeout=10)
        if response.status >= 500:
            log(f"ALERT {name} returned server error {response.status}: {url}")
            return False
        log(f"OK {name} returned {response.status}: {url}")
        return True
    except HTTPError as exc:
        if exc.code >= 500:
            log(f"ALERT {name} returned server error {exc.code}: {url}")
            return False
        log(f"OK {name} returned {exc.code}: {url}")
        return True
    except URLError as exc:
        log(f"ALERT {name} probe failed: {url} ({exc})")
        return False


def main() -> int:
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    checks = [
        (f"{base_url}/blog/", "blog_home"),
        (f"{base_url}/users/login/", "login_page"),
    ]
    ok = all(check_url(url, name) for url, name in checks)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
