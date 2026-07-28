#!/usr/bin/env python3
"""Recent albums

Run this on the server after SSH login:
    cd /var/www/my_site_prod_repo_new
    docker compose -f docker-compose.prod.yml exec -T web python database_commands/orm__recent_albums.py
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_site.settings.prod")

import django

django.setup()


def main() -> None:
    from images.models import Album
    rows = list(
        Album.objects.select_related("uploaded_by")
        .order_by("-created")
        .values("id", "title", "uploaded_by__username", "created")[:10]
    )
    print(rows)


if __name__ == "__main__":
    main()
