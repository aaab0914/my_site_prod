#!/usr/bin/env python3
"""Users holding DRF auth tokens

Run this on the server after SSH login:
    cd /var/www/my_site_prod_repo_new
    docker compose -f docker-compose.prod.yml exec -T web python database_commands/orm__users_with_api_tokens.py
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_site.settings.prod")

import django

django.setup()


def main() -> None:
    from rest_framework.authtoken.models import Token
    rows = list(
        Token.objects.select_related("user")
        .order_by("user__username")
        .values("user__username", "created")[:20]
    )
    print(rows)


if __name__ == "__main__":
    main()
