import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.db import OperationalError, ProgrammingError
from django.db.models.signals import post_migrate


logger = logging.getLogger(__name__)
_BOOTSTRAP_CONNECTED = False


def ensure_default_site(**kwargs):
    domain = getattr(settings, "DEFAULT_SITE_DOMAIN", "localhost:8000")
    name = getattr(settings, "DEFAULT_SITE_NAME", "localhost")
    try:
        site, created = Site.objects.update_or_create(
            id=settings.SITE_ID,
            defaults={"domain": domain, "name": name},
        )
    except (OperationalError, ProgrammingError) as exc:
        logger.warning("Failed to ensure default Site object: %s", exc)
        return None
    if created:
        logger.info("Created default Site id=%s domain=%s", site.id, site.domain)
    return site


def connect_site_bootstrap():
    global _BOOTSTRAP_CONNECTED
    if _BOOTSTRAP_CONNECTED:
        return
    post_migrate.connect(ensure_default_site, dispatch_uid="my_site.ensure_default_site")
    _BOOTSTRAP_CONNECTED = True
