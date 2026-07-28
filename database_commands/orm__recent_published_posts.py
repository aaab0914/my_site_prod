#!/usr/bin/env python3
"""Recent published blog posts

Run this on the server after SSH login:
    cd /var/www/my_site_prod_repo_new
    docker compose -f docker-compose.prod.yml exec -T web python database_commands/orm__recent_published_posts.py
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_site.settings.prod")

import django

django.setup()


def main() -> None:
    from blog.models import Post
    rows = list(
        Post.published.select_related("author")
        .order_by("-publish")
        .values("id", "title", "slug", "author__username", "publish")[:10]
    )
    print(rows)


if __name__ == "__main__":
    main()
