#!/usr/bin/env python3
"""Duplicate slugs on the same publish day

Run this on the server after SSH login:
    cd /var/www/my_site_prod_repo_new
    docker compose -f docker-compose.prod.yml exec -T web python database_commands/orm__duplicate_slugs_same_day.py
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_site.settings.prod")

import django

django.setup()


def main() -> None:
    from django.db.models import Count
    from django.db.models.functions import TruncDate
    from blog.models import Post
    rows = list(
        Post.objects.annotate(publish_day=TruncDate("publish"))
        .values("slug", "publish_day")
        .annotate(row_count=Count("id"))
        .filter(row_count__gt=1)
        .order_by("-row_count", "slug")[:10]
    )
    print(rows)


if __name__ == "__main__":
    main()
