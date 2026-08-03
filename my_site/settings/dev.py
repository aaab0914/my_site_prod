from copy import deepcopy
import os

from .base import *  # noqa: F401,F403


DEBUG = True

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "TIMEOUT": 60 * 60 * 24 * 30,
    }
}

TEMPLATES[0]["APP_DIRS"] = False
TEMPLATES[0]["OPTIONS"]["loaders"] = [
    "my_site.template_loaders.RedisFilesystemLoader",
    "my_site.template_loaders.RedisAppDirectoriesLoader",
]

LOGGING = deepcopy(LOGGING)

LOGGING["handlers"]["file"] = {
    "level": "INFO",
    "class": "my_site.logging_utils.DailyMonthlyFileHandler",
    "log_dir": str(LOG_DIR),
    "filename_prefix": "django",
    "formatter": "verbose",
}
LOGGING["handlers"]["error_file"] = {
    "level": "WARNING",
    "class": "my_site.logging_utils.DailyMonthlyFileHandler",
    "log_dir": str(LOG_DIR),
    "filename_prefix": "error",
    "formatter": "verbose",
}
if os.environ.get("RUNNING_IN_DOCKER", "").lower() == "true":
    LOGGING["handlers"].pop("file", None)
    LOGGING["handlers"].pop("error_file", None)
    LOGGING["loggers"]["django"]["handlers"] = ["console"]
    LOGGING["loggers"]["django.request"]["handlers"] = ["console"]
    LOGGING["loggers"]["blog"]["handlers"] = ["console"]
    LOGGING["loggers"]["users"]["handlers"] = ["console"]
else:
    LOGGING["loggers"]["django"]["handlers"] = ["console", "file", "error_file"]
    LOGGING["loggers"]["django.request"]["handlers"] = ["console", "file", "error_file"]
    LOGGING["loggers"]["blog"]["handlers"] = ["console", "file"]
    LOGGING["loggers"]["users"]["handlers"] = ["console", "file"]
