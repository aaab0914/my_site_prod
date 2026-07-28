import logging

from django.apps import AppConfig


logger = logging.getLogger(__name__)


class BlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "blog"

    def ready(self):
        try:
            from . import signals  # noqa: F401
            from . import documents  # noqa: F401
        except ImportError as exc:
            logger.warning("Failed to import blog signals: %s", exc)
        try:
            import my_site.media_signals  # noqa: F401
        except ImportError as exc:
            logger.warning("Failed to import media signals: %s", exc)
        try:
            import my_site.delete_guards  # noqa: F401
        except ImportError as exc:
            logger.warning("Failed to import delete guards: %s", exc)
        try:
            from my_site.site_bootstrap import connect_site_bootstrap
            connect_site_bootstrap()
        except ImportError as exc:
            logger.warning("Failed to import site bootstrap: %s", exc)
