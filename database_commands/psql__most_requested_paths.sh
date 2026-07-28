#!/usr/bin/env bash
set -euo pipefail

# Most requested paths in audit logs
# Run this on the server after SSH login:
#   cd /var/www/my_site_prod_repo_new
#   bash database_commands/psql__most_requested_paths.sh

cd /var/www/my_site_prod_repo_new
docker compose -f docker-compose.prod.yml exec -T db           sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f -'           < database_commands/sql__most_requested_paths.sql
