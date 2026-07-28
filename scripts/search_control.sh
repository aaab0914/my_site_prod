#!/bin/sh
set -eu
cd /var/www/my_site_prod_repo_new
exec docker compose -f docker-compose.prod.yml exec -T web python manage.py search_control "$@"
