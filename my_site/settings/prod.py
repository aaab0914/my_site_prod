from copy import deepcopy

from .base import *

DEBUG = False

SECURE_REFERRER_POLICY = config("SECURE_REFERRER_POLICY", default="same-origin")
SECURE_BROWSER_XSS_FILTER = config("SECURE_BROWSER_XSS_FILTER", default=True, cast=bool)
SECURE_CROSS_ORIGIN_OPENER_POLICY = config(
    "SECURE_CROSS_ORIGIN_OPENER_POLICY",
    default="same-origin",
)
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=True, cast=bool)
SESSION_COOKIE_SAMESITE = config("SESSION_COOKIE_SAMESITE", default="Lax")
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=True, cast=bool)
CSRF_COOKIE_SAMESITE = config("CSRF_COOKIE_SAMESITE", default="Lax")
CSRF_COOKIE_HTTPONLY = config("CSRF_COOKIE_HTTPONLY", default=True, cast=bool)
SESSION_COOKIE_HTTPONLY = config("SESSION_COOKIE_HTTPONLY", default=True, cast=bool)
SECURE_COOKIE_NAME_PREFIX = config("SECURE_COOKIE_NAME_PREFIX", default="__Secure-")
SESSION_COOKIE_NAME = f"{SECURE_COOKIE_NAME_PREFIX}sessionid"
CSRF_COOKIE_NAME = f"{SECURE_COOKIE_NAME_PREFIX}csrftoken"
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True, cast=bool
)
SECURE_HSTS_PRELOAD = config("SECURE_HSTS_PRELOAD", default=True, cast=bool)

MEDIA_SYNC_INTERVAL_SECONDS = config(
    "MEDIA_SYNC_INTERVAL_SECONDS", default=300, cast=int
)
MEDIA_SYNC_ENABLED = config("MEDIA_SYNC_ENABLED", default=False, cast=bool)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "TIMEOUT": 60 * 60 * 24 * 30,  # 30 days
    }
}

TEMPLATES[0]["APP_DIRS"] = False
TEMPLATES[0]["OPTIONS"]["loaders"] = [
    "my_site.template_loaders.RedisFilesystemLoader",
    "my_site.template_loaders.RedisAppDirectoriesLoader",
]


LOGGING = deepcopy(LOGGING)

LOGGING["filters"] = LOGGING.get("filters", {})
LOGGING["filters"]["skip_noisy_404"] = {
    "()": "my_site.logging_utils.SkipNoisy404Filter",
}
LOGGING["filters"]["below_warning"] = {
    "()": "my_site.logging_utils.MaxLevelFilter",
    "level": "WARNING",
}

LOGGING["handlers"]["file"] = {
    "level": "INFO",
    "class": "my_site.logging_utils.DailyMonthlyFileHandler",
    "log_dir": str(LOG_DIR),
    "filename_prefix": "django",
    "formatter": "verbose",
    "filters": ["skip_noisy_404", "below_warning"],
}
LOGGING["handlers"]["error_file"] = {
    "level": "WARNING",
    "class": "my_site.logging_utils.DailyMonthlyFileHandler",
    "log_dir": str(LOG_DIR),
    "filename_prefix": "django-error",
    "formatter": "verbose",
    "filters": ["skip_noisy_404"],
}
LOGGING["handlers"]["celery_file"] = {
    "level": "INFO",
    "class": "my_site.logging_utils.DailyMonthlyFileHandler",
    "log_dir": str(LOG_DIR),
    "filename_prefix": "celery",
    "formatter": "verbose",
}

LOGGING["loggers"]["django.db.backends"] = {
    "handlers": ["console"],
    "level": "DEBUG",
    "propagate": False,
}

LOGGING["loggers"]["django"]["handlers"] = ["console", "file", "error_file"]
LOGGING["loggers"]["django.request"]["handlers"] = ["console", "error_file"]
LOGGING["loggers"]["blog"]["handlers"] = ["console", "file", "error_file"]
LOGGING["loggers"]["users"]["handlers"] = ["console", "file", "error_file"]
LOGGING["loggers"]["celery"]["handlers"] = ["console", "celery_file", "error_file"]
LOGGING["loggers"]["celery.app.trace"] = {
    "handlers": ["console", "celery_file", "error_file"],
    "level": "INFO",
    "propagate": False,
}
LOGGING["loggers"]["celery.redirected"] = {
    "handlers": ["console", "celery_file", "error_file"],
    "level": "INFO",
    "propagate": False,
}

# ============================================================================
# SEARCH OVERRIDES (Production)
# ============================================================================
# PostgreSQL full-text search tuning for production.

# Higher threshold in production to reduce low-relevance results
SEARCH_MIN_RANK = config("SEARCH_MIN_RANK", default=0.05, cast=float)

# Pagination size
SEARCH_PAGE_SIZE = config("SEARCH_PAGE_SIZE", default=20, cast=int)

if TESTING:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-suite",
        }
    }

MIDDLEWARE = [
    mw for mw in MIDDLEWARE if mw != "my_site.media_sync_middleware.MediaSyncMiddleware"
]

# ============================================================================
# PASSWORD HASHING (use Argon2 for speed + security)
# ============================================================================

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]