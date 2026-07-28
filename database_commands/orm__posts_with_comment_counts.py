#!/usr/bin/env python3
"""Posts with comment counts

Run this on the server after SSH login:
    cd /var/www/my_site_prod_repo_new
    docker compose -f docker-compose.prod.yml exec -T web python database_commands/orm__posts_with_comment_counts.py
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_site.settings.prod")

import django

django.setup()


def main() -> None:
    from django.db.models import Count
    from blog.models import Post
    rows = list(
        Post.objects.annotate(comment_count=Count("comments"))
        .order_by("-comment_count", "-publish")
        .values("id", "title", "comment_count")[:10]
    )
    print(rows)


if __name__ == "__main__":
    main()
