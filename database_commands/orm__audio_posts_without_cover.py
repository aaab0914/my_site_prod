#!/usr/bin/env python3
"""Audio uploads without cover images

Run this on the server after SSH login:
    cd /var/www/my_site_prod_repo_new
    docker compose -f docker-compose.prod.yml exec -T web python database_commands/orm__audio_posts_without_cover.py
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_site.settings.prod")

import django

django.setup()


def main() -> None:
    from blog.models import AudioPost
    rows = list(
        AudioPost.objects.select_related("uploaded_by")
        .filter(cover_image__isnull=True)
        .order_by("-created")
        .values("id", "music_name", "uploaded_by__username", "created")[:10]
    )
    print(rows)


if __name__ == "__main__":
    main()
