
set -e
cd /var/www/my_site_prod_repo_new
echo '=== MIGRATION STATUS BLOG ==='
docker exec my_site_prod_repo-web-1 python manage.py showmigrations blog
echo '=== COMMENT TABLE COLUMNS ==='
docker exec my_site_prod_repo-db-1 psql -U my_site_user -d my_site_db -c "\d blog_comment"
echo '=== APPLIED BLOG MIGRATIONS ==='
docker exec my_site_prod_repo-db-1 psql -U my_site_user -d my_site_db -c "select app, name, applied from django_migrations where app='blog' order by name;"
echo '=== MIGRATION FILE 0014 ==='
docker exec my_site_prod_repo-web-1 sh -lc "sed -n '1,220p' /code/blog/migrations/0014_comment_author_fk.py"
