#!/usr/bin/env python3
"""Users missing profile rows

Run this on the server after SSH login:
    cd /var/www/my_site_prod_repo_new
    docker compose -f docker-compose.prod.yml exec -T web python database_commands/orm__users_without_profiles.py
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_site.settings.prod")

import django

django.setup()


def main() -> None:
    from django.contrib.auth.models import User
    rows = list(
        User.objects.filter(profile__isnull=True)
        .order_by("id")
        .values("id", "username", "email")[:20]
    )
    print(rows)


if __name__ == "__main__":
    main()
