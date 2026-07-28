#!/usr/bin/env python3
"""Most used tags on blog posts

Run this on the server after SSH login:
    cd /var/www/my_site_prod_repo_new
    docker compose -f docker-compose.prod.yml exec -T web python database_commands/orm__most_used_tags.py
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_site.settings.prod")

import django

django.setup()


def main() -> None:
    from django.db.models import Count
    from taggit.models import Tag
    rows = list(
        Tag.objects.annotate(post_count=Count("taggit_taggeditem_items"))
        .order_by("-post_count", "name")
        .values("id", "name", "slug", "post_count")[:10]
    )
    print(rows)


if __name__ == "__main__":
    main()
