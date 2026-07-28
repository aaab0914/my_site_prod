#!/usr/bin/env python3
"""Audit entries with 5xx responses

Run this on the server after SSH login:
    cd /var/www/my_site_prod_repo_new
    docker compose -f docker-compose.prod.yml exec -T web python database_commands/orm__audit_server_errors.py
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_site.settings.prod")

import django

django.setup()


def main() -> None:
    from blog.models import AuditLog
    rows = list(
        AuditLog.objects.filter(status_code__gte=500)
        .order_by("-timestamp")
        .values("id", "method", "path", "status_code", "timestamp")[:20]
    )
    print(rows)


if __name__ == "__main__":
    main()
