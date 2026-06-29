from pathlib import Path
import sys
import os

from decouple import AutoConfig


PROJECT_ROOT = Path(__file__).resolve().parent
config = AutoConfig(search_path=str(PROJECT_ROOT))


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    sys.exit(1)


def main() -> int:
    env_path = PROJECT_ROOT / ".env"
    env_source = env_path if env_path.exists() else "process environment"

    required_keys = [
        "SECRET_KEY",
        "ALLOWED_HOSTS",
        "CSRF_TRUSTED_ORIGINS",
        "DB_PASSWORD",
        "SECURE_SSL_REDIRECT",
        "SESSION_COOKIE_SECURE",
        "CSRF_COOKIE_SECURE",
        "SESSION_COOKIE_HTTPONLY",
        "CSRF_COOKIE_HTTPONLY",
        "SECURE_HSTS_SECONDS",
        "SECURE_HSTS_INCLUDE_SUBDOMAINS",
        "SECURE_HSTS_PRELOAD",
    ]
    missing_keys = [key for key in required_keys if not os.environ.get(key) and not env_path.exists()]
    if missing_keys:
        fail(f"Missing required production environment variables: {', '.join(missing_keys)}")

    debug = config("DEBUG", cast=bool, default=False)
    if debug:
        fail("Production environment must not run with DEBUG=True.")

    secret_key = config("SECRET_KEY", default="")
    if len(secret_key.strip()) < 32 or "change-me" in secret_key.lower():
        fail("SECRET_KEY is too weak or still uses a placeholder value.")

    allowed_hosts = [host.strip() for host in config("ALLOWED_HOSTS", default="").split(",") if host.strip()]
    if not allowed_hosts:
        fail("ALLOWED_HOSTS must not be empty.")
    if "*" in allowed_hosts:
        fail("ALLOWED_HOSTS must not contain '*'.")

    allowed_hosts = [host.strip() for host in config("ALLOWED_HOSTS", default="").split(",") if host.strip()]
    csrf_origins = [origin.strip() for origin in config("CSRF_TRUSTED_ORIGINS", default="").split(",") if origin.strip()]
    if not csrf_origins:
        fail("CSRF_TRUSTED_ORIGINS must not be empty in production.")

    localhost_only_http = {"http://localhost", "http://127.0.0.1"}
    non_local_origins = [origin for origin in csrf_origins if origin not in localhost_only_http]
    if any(not origin.startswith("https://") for origin in non_local_origins):
        fail("Non-local CSRF_TRUSTED_ORIGINS must use https:// origins in production.")

    required_true_bools = [
        "SECURE_SSL_REDIRECT",
        "SESSION_COOKIE_SECURE",
        "CSRF_COOKIE_SECURE",
        "SESSION_COOKIE_HTTPONLY",
        "CSRF_COOKIE_HTTPONLY",
    ]
    allow_local_http = any(host in {"localhost", "127.0.0.1"} for host in allowed_hosts)
    for key in required_true_bools:
        value = config(key, cast=bool, default=False)
        if allow_local_http and key in {"SECURE_SSL_REDIRECT", "SESSION_COOKIE_SECURE", "CSRF_COOKIE_SECURE"}:
            continue
        if not value:
            fail(f"{key} must be True in production.")

    hsts_seconds = config("SECURE_HSTS_SECONDS", cast=int, default=0)
    if hsts_seconds < 31536000:
        fail("SECURE_HSTS_SECONDS must be at least 31536000 in production.")

    for key in ("SECURE_HSTS_INCLUDE_SUBDOMAINS", "SECURE_HSTS_PRELOAD"):
        if not config(key, cast=bool, default=False):
            fail(f"{key} must be True in production.")

    db_password = config("DB_PASSWORD", default="")
    if len(db_password.strip()) < 12 or "change-me" in db_password.lower():
        fail("DB_PASSWORD is too weak or still uses a placeholder value.")

    print(f"Production environment validation passed for {env_source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
