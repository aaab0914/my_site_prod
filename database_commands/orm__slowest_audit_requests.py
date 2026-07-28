#!/usr/bin/env python3
"""Slowest audit log requests

Run this on the server after SSH login:
    cd /var/www/my_site_prod_repo_new
    docker compose -f docker-compose.prod.yml exec -T web python database_commands/orm__slowest_audit_requests.py
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_site.settings.prod")

import django

django.setup()


def main() -> None:
    from blog.models import AuditLog
    rows = list(
        AuditLog.objects.select_related("user")
        .order_by("-response_time", "-timestamp")
        .values("id", "method", "path", "status_code", "response_time", "timestamp")[:10]
    )
    print(rows)


if __name__ == "__main__":
    main()
