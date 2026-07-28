#!/usr/bin/env python3
"""Albums with image counts

Run this on the server after SSH login:
    cd /var/www/my_site_prod_repo_new
    docker compose -f docker-compose.prod.yml exec -T web python database_commands/orm__albums_with_image_counts.py
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_site.settings.prod")

import django

django.setup()


def main() -> None:
    from django.db.models import Count
    from images.models import Album
    rows = list(
        Album.objects.annotate(image_count=Count("images"))
        .order_by("-image_count", "-created")
        .values("id", "title", "image_count", "created")[:10]
    )
    print(rows)


if __name__ == "__main__":
    main()
