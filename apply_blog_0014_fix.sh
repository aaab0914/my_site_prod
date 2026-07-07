
set -e
cd /var/www/my_site_prod_repo_new
backup="/root/codex_backups/my_site_db_before_blog_0014_$(date +%Y%m%d_%H%M%S).sql"
mkdir -p /root/codex_backups
echo "=== BACKUP ==="
docker exec my_site_prod_repo-db-1 pg_dump -U my_site_user -d my_site_db > "$backup"
ls -lh "$backup"
echo "=== APPLY MIGRATION ==="
docker exec my_site_prod_repo-web-1 python manage.py migrate blog 0014
echo "=== VERIFY MIGRATIONS ==="
docker exec my_site_prod_repo-web-1 python manage.py showmigrations blog | tail -n 5
echo "=== VERIFY COMMENT TABLE ==="
docker exec my_site_prod_repo-db-1 psql -U my_site_user -d my_site_db -c "\d blog_comment"
echo "=== VERIFY URLS ==="
curl -k -I -sS https://rgavanp.kdns.fr/blog/2026/7/2/post-20260702124526/ || true
curl -k -I -sS https://rgavanp.kdns.fr/blog/2026/7/2/there-is-nobody-here-anymore-the-silence-of-virtual-places/ || true
echo "=== DJANGO CLIENT VERIFY ==="
docker exec my_site_prod_repo-web-1 python manage.py shell -c "from django.test import Client; c=Client(HTTP_HOST='rgavanp.kdns.fr'); urls=['/blog/2026/7/2/post-20260702124526/','/blog/2026/7/2/there-is-nobody-here-anymore-the-silence-of-virtual-places/'];
for url in urls:
    r=c.get(url)
    print(url, r.status_code)"
