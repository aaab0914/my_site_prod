#!/usr/bin/env python3
"""Posts with the longest bodies

Run this on the server after SSH login:
    cd /var/www/my_site_prod_repo_new
    docker compose -f docker-compose.prod.yml exec -T web python database_commands/orm__longest_post_bodies.py
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_site.settings.prod")

import django

django.setup()


def main() -> None:
    from django.db.models.functions import Length
    from blog.models import Post
    rows = list(
        Post.objects.annotate(body_length=Length("body"))
        .order_by("-body_length", "-publish")
        .values("id", "title", "body_length", "publish")[:10]
    )
    print(rows)


if __name__ == "__main__":
    main()
