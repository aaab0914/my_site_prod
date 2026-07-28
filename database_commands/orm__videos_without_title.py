#!/usr/bin/env python3
"""Video uploads without explicit titles

Run this on the server after SSH login:
    cd /var/www/my_site_prod_repo_new
    docker compose -f docker-compose.prod.yml exec -T web python database_commands/orm__videos_without_title.py
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_site.settings.prod")

import django

django.setup()


def main() -> None:
    from blog.models import VideoPost
    rows = list(
        VideoPost.objects.select_related("uploaded_by")
        .filter(title="")
        .order_by("-created")
        .values("id", "video_file", "uploaded_by__username", "created")[:10]
    )
    print(rows)


if __name__ == "__main__":
    main()
