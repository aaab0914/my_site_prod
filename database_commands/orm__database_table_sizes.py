#!/usr/bin/env python3
"""Largest database tables

Run this on the server after SSH login:
    cd /var/www/my_site_prod_repo_new
    docker compose -f docker-compose.prod.yml exec -T web python database_commands/orm__database_table_sizes.py
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_site.settings.prod")

import django

django.setup()


def main() -> None:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute(
            '''
            SELECT relname AS table_name,
                   pg_size_pretty(pg_total_relation_size(relid)) AS total_size
            FROM pg_catalog.pg_statio_user_tables
            ORDER BY pg_total_relation_size(relid) DESC
            LIMIT 20
            '''
        )
        print(cursor.fetchall())


if __name__ == "__main__":
    main()
