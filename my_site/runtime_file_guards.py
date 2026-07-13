from pathlib import Path

from django.conf import settings
from django.core.exceptions import PermissionDenied


PROTECTED_RUNTIME_ROOT_NAMES = ("logs", "backups")
PROTECTED_DATABASE_PATH_PARTS = (
    "postgres_data",
    "var/lib/postgresql",
    "pg_wal",
    "pgdata",
)
PROTECTED_LOG_SUFFIXES = (".log",)
PROTECTED_DATABASE_SUFFIXES = (".sql", ".sqlite3", ".db", ".dump", ".bak")


def _project_base_dir():
    return Path(getattr(settings, "BASE_DIR", Path.cwd())).resolve()


def _protected_runtime_roots():
    base_dir = _project_base_dir()
    return [base_dir / root_name for root_name in PROTECTED_RUNTIME_ROOT_NAMES]


def normalize_runtime_path(path_value):
    candidate = Path(path_value)
    if not candidate.is_absolute():
        candidate = _project_base_dir() / candidate
    return candidate.resolve(strict=False)


def is_protected_runtime_path(path_value):
    candidate = normalize_runtime_path(path_value)

    for protected_root in _protected_runtime_roots():
        try:
            candidate.relative_to(protected_root)
            return True
        except ValueError:
            pass

    candidate_text = candidate.as_posix().lower()
    if any(part in candidate_text for part in PROTECTED_DATABASE_PATH_PARTS):
        return True

    if candidate.suffix.lower() in PROTECTED_LOG_SUFFIXES + PROTECTED_DATABASE_SUFFIXES:
        return True

    return False


def ensure_runtime_file_not_protected(path_value, action="delete"):
    if is_protected_runtime_path(path_value):
        raise PermissionDenied(
            f"{action.capitalize()} is not allowed for protected database or log files: {path_value}"
        )
