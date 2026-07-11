from .base import *  # noqa: F401,F403


DEBUG = False

SECURE_REFERRER_POLICY = config("SECURE_REFERRER_POLICY", default="same-origin")
SECURE_BROWSER_XSS_FILTER = config("SECURE_BROWSER_XSS_FILTER", default=True, cast=bool)
SECURE_CROSS_ORIGIN_OPENER_POLICY = config(
    "SECURE_CROSS_ORIGIN_OPENER_POLICY",
    default="same-origin",
)
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=True, cast=bool)
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=True, cast=bool)
CSRF_COOKIE_HTTPONLY = config("CSRF_COOKIE_HTTPONLY", default=True, cast=bool)
SESSION_COOKIE_HTTPONLY = config("SESSION_COOKIE_HTTPONLY", default=True, cast=bool)
SECURE_COOKIE_NAME_PREFIX = config("SECURE_COOKIE_NAME_PREFIX", default="__Secure-")
SESSION_COOKIE_NAME = f"{SECURE_COOKIE_NAME_PREFIX}sessionid"
CSRF_COOKIE_NAME = f"{SECURE_COOKIE_NAME_PREFIX}csrftoken"
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True, cast=bool)
SECURE_HSTS_PRELOAD = config("SECURE_HSTS_PRELOAD", default=True, cast=bool)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "TIMEOUT": 120,
    }
}

if TESTING:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-suite",
        }
    }
