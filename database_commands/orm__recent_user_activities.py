#!/usr/bin/env python3
"""Recent user activities

Run this on the server after SSH login:
    cd /var/www/my_site_prod_repo_new
    docker compose -f docker-compose.prod.yml exec -T web python database_commands/orm__recent_user_activities.py
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_site.settings.prod")

import django

django.setup()


def main() -> None:
    from users.models import UserActivity
    rows = list(
        UserActivity.objects.select_related("user")
        .order_by("-timestamp")
        .values("id", "user__username", "action", "ip_address", "timestamp")[:20]
    )
    print(rows)


if __name__ == "__main__":
    main()
