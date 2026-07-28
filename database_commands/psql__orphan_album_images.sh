#!/usr/bin/env bash
set -euo pipefail

# Album images not linked to an album
# Run this on the server after SSH login:
#   cd /var/www/my_site_prod_repo_new
#   bash database_commands/psql__orphan_album_images.sh

cd /var/www/my_site_prod_repo_new
docker compose -f docker-compose.prod.yml exec -T db           sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f -'           < database_commands/sql__orphan_album_images.sql
