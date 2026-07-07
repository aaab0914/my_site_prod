
set -e
cd /var/www/my_site_prod_repo_new
docker compose -p my_site_prod_repo_new -f docker-compose.prod.yml down
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep 'my_site_prod_repo' || true
