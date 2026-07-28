#!/usr/bin/env python3
"""Token regeneration cooldown status

Run this on the server after SSH login:
    cd /var/www/my_site_prod_repo_new
    docker compose -f docker-compose.prod.yml exec -T web python database_commands/orm__token_regeneration_status.py
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_site.settings.prod")

import django

django.setup()


def main() -> None:
    from users.models import Profile
    rows = []
    for profile in Profile.objects.select_related("user").order_by("user__username")[:20]:
        rows.append({
            "user": profile.user.username,
            "is_staff": profile.user.is_staff,
            "last_token_generated_at": profile.last_token_generated_at,
            "remaining_days": profile.get_token_regeneration_remaining_days(),
        })
    print(rows)


if __name__ == "__main__":
    main()
