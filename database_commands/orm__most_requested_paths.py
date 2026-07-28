#!/usr/bin/env python3
"""Most requested paths in audit logs

Run this on the server after SSH login:
    cd /var/www/my_site_prod_repo_new
    docker compose -f docker-compose.prod.yml exec -T web python database_commands/orm__most_requested_paths.py
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_site.settings.prod")

import django

django.setup()


def main() -> None:
    from django.db.models import Count
    from blog.models import AuditLog
    rows = list(
        AuditLog.objects.values("path")
        .annotate(hit_count=Count("id"))
        .order_by("-hit_count", "path")[:20]
    )
    print(rows)


if __name__ == "__main__":
    main()
