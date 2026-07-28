#!/usr/bin/env python3
"""Comments carrying uploaded images

Run this on the server after SSH login:
    cd /var/www/my_site_prod_repo_new
    docker compose -f docker-compose.prod.yml exec -T web python database_commands/orm__comments_with_images.py
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_site.settings.prod")

import django

django.setup()


def main() -> None:
    from blog.models import Comment
    rows = list(
        Comment.objects.select_related("post", "author")
        .exclude(image="")
        .exclude(image__isnull=True)
        .order_by("-created")
        .values("id", "post__title", "author__username", "image", "created")[:10]
    )
    print(rows)


if __name__ == "__main__":
    main()
