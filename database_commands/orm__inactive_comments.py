#!/usr/bin/env python3
"""Inactive comments for moderation

Run this on the server after SSH login:
    cd /var/www/my_site_prod_repo_new
    docker compose -f docker-compose.prod.yml exec -T web python database_commands/orm__inactive_comments.py
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_site.settings.prod")

import django

django.setup()


def main() -> None:
    from blog.models import Comment
    rows = list(
        Comment.objects.select_related("post", "author")
        .filter(active=False)
        .order_by("-updated")
        .values("id", "post__title", "author__username", "updated")[:10]
    )
    print(rows)


if __name__ == "__main__":
    main()
