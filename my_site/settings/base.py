# base.py - Django project base settings module
# This file contains common settings shared across all environments (development, production, testing)
# Environment-specific settings should be placed in separate files (dev.py, prod.py, test.py)

# ============================================================================
# IMPORTS
# ============================================================================

import os  # Provides operating system independent functionality, used to read environment variables
import sys
from pathlib import (
    Path,
)  # Object-oriented filesystem path handling (modern replacement for os.path)

import sentry_sdk
from celery.schedules import crontab

# django-decouple: Used to manage settings via environment variables, keeping secrets out of version control
from decouple import (
    Csv,
    config,
)  # Csv: casts environment variables to lists; config: reads env variables with type casting
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration

# ============================================================================
# PATH CONFIGURATION
# ============================================================================

# BASE_DIR: The absolute path to the project root directory
# __file__ is the current file's path, resolved to absolute path, then go up 3 levels
# This allows consistent path references regardless of where the app is run
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TESTING = "test" in sys.argv

# ============================================================================
# SECURITY & CORE SETTINGS
# ============================================================================

# SECRET_KEY: Critical cryptographic key used for sessions, password reset tokens, and security signatures
# Must be set in environment variables; never commit to version control
SECRET_KEY = config("SECRET_KEY")

# DEBUG: Enables verbose error pages and automatic static file serving
# Should ALWAYS be False in production; True only for local development
# Cast to boolean using decouple's cast parameter
DEBUG = config("DEBUG", cast=bool, default=False)

# ALLOWED_HOSTS: List of domain names/hostnames that Django can serve
# Prevents HTTP Host header attacks; values must be comma-separated (e.g., "example.com,www.example.com")
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())
if os.environ.get("RUNNING_IN_DOCKER"):
    for internal_host in ("web", "nginx", "localhost", "127.0.0.1"):
        if internal_host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(internal_host)

# CSRF_TRUSTED_ORIGINS: Domains allowed to submit POST requests (for CSRF protection)
# Required when using reverse proxies or when frontend is on different domain
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())

# SITE_ID: Identifies the current site when using Django's sites framework
# Required for sitemap generation and multi-site support
SITE_ID = 1
ADMIN_URL_PATH = config("ADMIN_URL_PATH", default="secure-console-7f9a2c-admin/")

# ============================================================================
# INSTALLED APPLICATIONS
# ============================================================================

# INSTALLED_APPS: All Django apps and third-party packages used in this project
# Order matters: apps listed first have template/static file precedence
INSTALLED_APPS = [
    # Built-in Django apps:
    "django.contrib.admin",  # Administration interface for managing site content
    "django.contrib.auth",  # User authentication and permissions system
    "django.contrib.contenttypes",  # Generic foreign key support (required for permissions)
    "django.contrib.sessions",  # Session management for tracking users
    "django.contrib.messages",  # One-time notification framework
    "django.contrib.staticfiles",  # Static file management (CSS, JS, images)
    # Django contrib features:
    "django.contrib.sites",  # Multi-site management framework (used for sitemaps)
    "django.contrib.sitemaps",  # XML sitemap generation for SEO
    "django.contrib.postgres",  # PostgreSQL-specific features (full-text search, etc.)
    # Third-party packages:
    "django_extensions",  # Additional management commands and tools for development
    "rest_framework",  # Django REST Framework for building Web APIs
    "django_filters",  # Advanced queryset filtering for REST APIs
    "rest_framework.authtoken",  # Token-based authentication for REST API
    # Custom project apps (defined with AppConfig for more control):
    "blog.apps.BlogConfig",  # Blog application with posts, tags, and audio features
    "images.apps.ImagesConfig",  # Image upload and management application
    "users.apps.UsersConfig",  # User registration, login, profiles, and account management
    "taggit",  # Simple tagging library for Django (used for post tags)
    "markdownx",  # Markdown editing and rendering for blog posts
    "my_site",  # Project package so Celery autodiscover_tasks finds my_site.tasks
    # REMOVED: "django_elasticsearch_dsl"  (replaced by PostgreSQL full-text search)
]

# ============================================================================
# DJANGO REST FRAMEWORK CONFIGURATION
# ============================================================================

# REST_FRAMEWORK: Global configuration for Django REST Framework
REST_FRAMEWORK = {
    # Authentication classes: determine how API clients are authenticated
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",  # Token-based auth (good for mobile/SPA)
        "rest_framework.authentication.SessionAuthentication",  # Session-based auth (good for browser API browsing)
    ],
    # Permission classes: determine what authenticated users can do
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",  # Read-only for anonymous, full access for auth'd users
    ],
}

# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================

# MIDDLEWARE: Ordered list of hooks that process requests/responses
# Order matters: each middleware wraps the next, processing order is top-to-bottom on request
MIDDLEWARE = [
    # Security middleware: Enforces various security measures (HTTPS, HSTS, etc.)
    "django.middleware.security.SecurityMiddleware",
    # Session middleware: Manages user sessions across requests
    "django.contrib.sessions.middleware.SessionMiddleware",
    # Common middleware: Handles broken links, URL rewriting, etc.
    "django.middleware.common.CommonMiddleware",
    # CSRF middleware: Protects against Cross-Site Request Forgery attacks
    "django.middleware.csrf.CsrfViewMiddleware",
    # Authentication middleware: Associates requests with authenticated users
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Messages middleware: Adds messages framework to the request
    "django.contrib.messages.middleware.MessageMiddleware",
    # X-Frame-Options middleware: Prevents clickjacking attacks
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Custom middleware: Enforces login requirement for protected URLs
    "my_site.middleware.LoginRequiredMiddleware",
    # Custom middleware: Logs user actions and API calls for audit trail
    # "my_site.audit_middleware.AuditLoggingMiddleware",
]

# ============================================================================
# URL & TEMPLATES CONFIGURATION
# ============================================================================

# ROOT_URLCONF: Python module containing root URL patterns
ROOT_URLCONF = "my_site.urls"

# TEMPLATES: Configuration for Django's template engine
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",  # Django template engine
        "DIRS": [
            str(BASE_DIR / "my_site" / "templates")
        ],  # Project-level templates such as the public homepage
        "APP_DIRS": True,  # Whether to look for templates inside each app's 'templates/' directory
        "OPTIONS": {
            "context_processors": [  # Functions that add variables to every template context
                "django.template.context_processors.request",  # Adds 'request' to template context
                "django.contrib.auth.context_processors.auth",  # Adds 'user' and 'perms' to context
                "django.contrib.messages.context_processors.messages",  # Adds 'messages' to context
            ],
        },
    },
]

# ============================================================================
# WSGI & ASGI APPLICATION
# ============================================================================

# WSGI_APPLICATION: WSGI callable for production servers (Gunicorn, uWSGI, etc.)
WSGI_APPLICATION = "my_site.wsgi.application"

# ASGI_APPLICATION: ASGI callable for async servers (Daphne, Uvicorn) - used for WebSockets
ASGI_APPLICATION = "my_site.asgi.application"

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# DATABASES: Connection configuration for PostgreSQL database
# Uses environment variables for security and portability
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",  # PostgreSQL backend
        "NAME": os.environ.get("DB_NAME"),  # Database name (from environment)
        "USER": os.environ.get("DB_USER"),  # Database user (from environment)
        "PASSWORD": os.environ.get(
            "DB_PASSWORD"
        ),  # Database password (from environment)
        # HOST: If running in Docker, use 'db' (service name); else use 'localhost'
        "HOST": os.environ.get(
            "DB_HOST", "db" if os.environ.get("RUNNING_IN_DOCKER") else "localhost"
        ),
        "PORT": os.environ.get("DB_PORT", "5432"),  # PostgreSQL default port
        "CONN_MAX_AGE": config("DB_CONN_MAX_AGE", default=60, cast=int),
        "CONN_HEALTH_CHECKS": True,
    }
}

REDIS_URL = config("REDIS_URL", default="redis://redis:6379/0")

# Cache Configuration
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "TIMEOUT": 300,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "CONNECTION_POOL_CLASS": "redis.BlockingConnectionPool",
            "CONNECTION_POOL_CLASS_KWARGS": {
                "max_connections": 50,
                "timeout": 20,
            },
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            "IGNORE_EXCEPTIONS": True,
        },
        "KEY_PREFIX": "mysite",
        "VERSION": 1,
    }
}

CELERY_BROKER_URL = config("CELERY_BROKER_URL", default=REDIS_URL)
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default=REDIS_URL)
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = config(
    "CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP",
    default=True,
    cast=bool,
)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = config("CELERY_TASK_TIME_LIMIT", default=30 * 60, cast=int)
CELERY_TASK_SOFT_TIME_LIMIT = config(
    "CELERY_TASK_SOFT_TIME_LIMIT", default=25 * 60, cast=int
)
CELERY_WORKER_SEND_TASK_EVENTS = config(
    "CELERY_WORKER_SEND_TASK_EVENTS", default=True, cast=bool
)
CELERY_TASK_SEND_SENT_EVENT = config(
    "CELERY_TASK_SEND_SENT_EVENT", default=True, cast=bool
)
CELERY_RESULT_EXTENDED = config("CELERY_RESULT_EXTENDED", default=True, cast=bool)
MEDIA_SYNC_BEAT_MINUTES = config("MEDIA_SYNC_BEAT_MINUTES", default=5, cast=int)
LOG_RETENTION_DAYS = config("LOG_RETENTION_DAYS", default=120, cast=int)
AUDIT_LOG_RETENTION_DAYS = config("AUDIT_LOG_RETENTION_DAYS", default=90, cast=int)
CELERY_BEAT_SCHEDULE = {
    "ensure-daily-runtime-logs": {
        "task": "my_site.tasks.ensure_daily_runtime_logs_task",
        "schedule": crontab(minute=1, hour=0),
    },
    "ping-blog-task-every-5-minutes": {
        "task": "blog.tasks.ping_blog_task",
        "schedule": crontab(minute="*/5"),
    },
    "purge-old-audit-logs-daily": {
        "task": "my_site.tasks.purge_old_audit_logs_task",
        "schedule": crontab(minute=15, hour=3),
        "kwargs": {"days": AUDIT_LOG_RETENTION_DAYS},
    },
    "purge-old-runtime-logs-daily": {
        "task": "my_site.tasks.purge_old_runtime_logs_task",
        "schedule": crontab(minute=25, hour=3),
        "kwargs": {"days": LOG_RETENTION_DAYS},
    },
}

# ============================================================================
# SEARCH CONFIGURATION (PostgreSQL Full-Text Search)
# ============================================================================
# Replaces the previous Elasticsearch-based search.
# Requires 'django.contrib.postgres' in INSTALLED_APPS and PostgreSQL >= 9.6.

# Field weights: A = highest, D = lowest
SEARCH_TITLE_WEIGHT = config("SEARCH_TITLE_WEIGHT", default="A")
SEARCH_CONTENT_WEIGHT = config("SEARCH_CONTENT_WEIGHT", default="B")
SEARCH_TAGS_WEIGHT = config("SEARCH_TAGS_WEIGHT", default="C")

# Minimum rank threshold: results below this are filtered out
SEARCH_MIN_RANK = config("SEARCH_MIN_RANK", default=0.01, cast=float)

# Pagination size for search results
SEARCH_PAGE_SIZE = config("SEARCH_PAGE_SIZE", default=20, cast=int)

# Search query type: plain / phrase / raw / websearch
SEARCH_QUERY_TYPE = config("SEARCH_QUERY_TYPE", default="websearch")

# ============================================================================
# AUTHENTICATION PASSWORD VALIDATORS
# ============================================================================

# AUTH_PASSWORD_VALIDATORS: Password strength validation rules
# Prevents users from choosing common or easily guessable passwords
if TESTING:
    PASSWORD_HASHERS = [
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    # Password can't be similar to user info
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"
    },  # Minimum length requirement
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"
    },  # Can't be commonly used password
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"
    },  # Can't be entirely numeric
]

# ============================================================================
# INTERNATIONALIZATION & TIME ZONE
# ============================================================================

# LANGUAGE_CODE: Default language for the site (affects translations, date formats)
LANGUAGE_CODE = "en-us"
# TIME_ZONE: Server's time zone (affects datetime storage and display)
TIME_ZONE = "UTC"
# USE_I18N: Whether to enable internationalization (multi-language support)
USE_I18N = True
# USE_TZ: Whether to use timezone-aware datetime objects
USE_TZ = True

# ============================================================================
# STATIC & MEDIA FILES
# ============================================================================

# STATIC_URL: URL prefix for serving static files (CSS, JS, images)
STATIC_URL = "/static/"
# STATICFILES_DIRS: Additional directories for static file collection
STATICFILES_DIRS = [BASE_DIR / "static"]  # Project-level static directory
# STATIC_ROOT: Destination directory for 'collectstatic' command (served by web server)
STATIC_ROOT = config("STATIC_ROOT", default=BASE_DIR / "staticfiles")

# MEDIA_URL: URL prefix for user-uploaded files
MEDIA_URL = "/media/"
# MEDIA_ROOT: Filesystem path for storing user-uploaded files
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_SYNC_INTERVAL_SECONDS = config(
    "MEDIA_SYNC_INTERVAL_SECONDS", default=10, cast=int
)
MEDIA_SYNC_ENABLED = config("MEDIA_SYNC_ENABLED", default=(not TESTING), cast=bool)

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# LOG_DIR: Directory for storing log files (automatically created if it doesn't exist)
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# LOGGING: Python logging configuration for the entire project
# All logs are output to console (stdout) for Docker-friendly logging
LOGGING = {
    "version": 1,  # Logging configuration version
    "disable_existing_loggers": False,  # Don't disable default Django loggers
    "formatters": {  # Define log message format
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {asctime} {message}",  # Simpler format for console output
            "style": "{",
        },
    },
    "handlers": {  # Where log messages are sent
        "console": {
            "level": "INFO",  # Log INFO level and above
            "class": "logging.StreamHandler",  # Output to stdout
            "formatter": "simple",  # Use simple format
        },
    },
    "loggers": {  # Configure specific loggers
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },  # Core Django logs
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },  # Request/response logs
        "blog": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },  # Blog app logs
        "users": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },  # Users app logs
        "celery": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

SENTRY_DSN = config("SENTRY_DSN", default="")
SENTRY_ENVIRONMENT = config(
    "SENTRY_ENVIRONMENT", default="development" if DEBUG else "production"
)
SENTRY_RELEASE = config("SENTRY_RELEASE", default="")
SENTRY_TRACES_SAMPLE_RATE = config("SENTRY_TRACES_SAMPLE_RATE", default=0.0, cast=float)
SENTRY_PROFILES_SAMPLE_RATE = config(
    "SENTRY_PROFILES_SAMPLE_RATE", default=0.0, cast=float
)

if SENTRY_DSN:
    sentry_options = {
        "dsn": SENTRY_DSN,
        "integrations": [DjangoIntegration(), CeleryIntegration()],
        "environment": SENTRY_ENVIRONMENT,
        "traces_sample_rate": SENTRY_TRACES_SAMPLE_RATE,
        "profiles_sample_rate": SENTRY_PROFILES_SAMPLE_RATE,
        "send_default_pii": False,
    }
    if SENTRY_RELEASE:
        sentry_options["release"] = SENTRY_RELEASE
    sentry_sdk.init(**sentry_options)

# ============================================================================
# SECURITY SETTINGS (HTTPS, SSL, HSTS)
# ============================================================================

# SECURE_PROXY_SSL_HEADER: Tells Django to trust the X-Forwarded-Proto header from proxy
# Required when running behind Nginx or other SSL-terminating proxies
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# SECURE_SSL_REDIRECT: Whether to redirect all HTTP requests to HTTPS
# Should be True in production; False in development
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=False, cast=bool)

# SESSION_COOKIE_SECURE: Whether session cookies should only be sent over HTTPS
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=False, cast=bool)

# CSRF_COOKIE_SECURE: Whether CSRF cookies should only be sent over HTTPS
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=False, cast=bool)

# SECURE_HSTS_SECONDS: HTTP Strict Transport Security (HSTS) duration in seconds
# Forces browsers to use HTTPS for the specified time
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=0, cast=int)

# SECURE_HSTS_INCLUDE_SUBDOMAINS: Whether HSTS policy applies to subdomains
SECURE_HSTS_INCLUDE_SUBDOMAINS = config(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False, cast=bool
)

# SECURE_HSTS_PRELOAD: Whether to opt-in to HSTS preload list (submitted to browsers)
SECURE_HSTS_PRELOAD = config("SECURE_HSTS_PRELOAD", default=False, cast=bool)

# SECURE_CONTENT_TYPE_NOSNIFF: Prevent browsers from MIME-sniffing content types
SECURE_CONTENT_TYPE_NOSNIFF = True

# X_FRAME_OPTIONS: Prevent clickjacking by preventing page from being framed
X_FRAME_OPTIONS = "DENY"

# ============================================================================
# FILE UPLOAD & DATA LIMITS
# ============================================================================

# UPLOAD_MAX_MEMORY_SIZE: Shared upper bound for request and file uploads.
UPLOAD_MAX_MEMORY_SIZE = config(
    "UPLOAD_MAX_MEMORY_SIZE", default=120 * 1024 * 1024, cast=int
)  # 120MB

# DATA_UPLOAD_MAX_MEMORY_SIZE: Maximum size of POST data (in bytes)
# Prevents large uploads from consuming too much memory
DATA_UPLOAD_MAX_MEMORY_SIZE = config(
    "DATA_UPLOAD_MAX_MEMORY_SIZE",
    default=UPLOAD_MAX_MEMORY_SIZE,
    cast=int,
)

# FILE_UPLOAD_MAX_MEMORY_SIZE: Keep large media uploads out of worker memory.
FILE_UPLOAD_MAX_MEMORY_SIZE = config(
    "FILE_UPLOAD_MAX_MEMORY_SIZE",
    default=2_621_440,  # Django's standard 2.5MB in-memory threshold.
    cast=int,
)

# ============================================================================
# URLS & DEFAULT FIELD
# ============================================================================

# LOGIN_URL: URL to redirect for login-required views (used by LoginRequiredMiddleware)
LOGIN_URL = "/users/login/"

# DEFAULT_AUTO_FIELD: Default primary key field type for models
# BigAutoField uses 64-bit integers (vs AutoField's 32-bit) for future scalability
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"