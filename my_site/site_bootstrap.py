import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.db import OperationalError, ProgrammingError


logger = logging.getLogger(__name__)


def ensure_default_site():
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
