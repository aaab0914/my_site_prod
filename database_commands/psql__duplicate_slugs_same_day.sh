#!/usr/bin/env bash
set -euo pipefail

# Duplicate slugs on the same publish day
# Run this on the server after SSH login:
#   cd /var/www/my_site_prod_repo_new
#   bash database_commands/psql__duplicate_slugs_same_day.sh

cd /var/www/my_site_prod_repo_new
docker compose -f docker-compose.prod.yml exec -T db           sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f -'           < database_commands/sql__duplicate_slugs_same_day.sql
