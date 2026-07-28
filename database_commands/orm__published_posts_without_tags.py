#!/usr/bin/env python3
"""Published posts without tags

Run this on the server after SSH login:
    cd /var/www/my_site_prod_repo_new
    docker compose -f docker-compose.prod.yml exec -T web python database_commands/orm__published_posts_without_tags.py
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_site.settings.prod")

import django

django.setup()


def main() -> None:
    from blog.models import Post
    rows = list(
        Post.published.filter(taggit_taggeditem_items__isnull=True)
        .values("id", "title", "slug", "publish")[:10]
    )
    print(rows)


if __name__ == "__main__":
    main()
