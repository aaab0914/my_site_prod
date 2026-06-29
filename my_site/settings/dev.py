from copy import deepcopy

from .base import *  # noqa: F401,F403


DEBUG = True

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
LOGGING["loggers"]["django"]["handlers"] = ["console", "file", "error_file"]
LOGGING["loggers"]["django.request"]["handlers"] = ["console", "file", "error_file"]
LOGGING["loggers"]["blog"]["handlers"] = ["console", "file"]
LOGGING["loggers"]["users"]["handlers"] = ["console", "file"]
