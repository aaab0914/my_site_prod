#!/usr/bin/env python3
"""Monthly content summary

Run this on the server after SSH login:
    cd /var/www/my_site_prod_repo_new
    docker compose -f docker-compose.prod.yml exec -T web python database_commands/orm__monthly_content_summary.py
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_site.settings.prod")

import django

django.setup()


def main() -> None:
    from django.db.models import Count
    from django.db.models.functions import TruncMonth
    from blog.models import Post, Comment
    post_rows = list(
        Post.objects.annotate(month=TruncMonth("publish"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("-month")[:12]
    )
    comment_rows = list(
        Comment.objects.annotate(month=TruncMonth("created"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("-month")[:12]
    )
    print({"posts": post_rows, "comments": comment_rows})


if __name__ == "__main__":
    main()
