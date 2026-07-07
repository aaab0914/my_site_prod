
set -e
cd /var/www/my_site_prod_repo_new
python3 -m py_compile blog/models.py
docker compose -p my_site_prod_repo -f docker-compose.prod.yml up -d --build web
sleep 12
docker exec my_site_prod_repo-web-1 python manage.py shell -c "from blog.models import Post; fixed=[]
for post in Post.objects.filter(slug='').order_by('id'):
    post.slug = post.build_slug()
    post.save(update_fields=['slug','updated'])
    fixed.append((post.id, post.title, post.slug))
print('fixed_blank_slugs=', fixed)
print('remaining_blank=', Post.objects.filter(slug='').count())"
echo '---CONTAINER_MODEL---'
docker exec my_site_prod_repo-web-1 sh -lc "grep -n 'def build_slug\|self.build_slug\|slugify(self.title' /code/blog/models.py"
echo '---HTTP_BLOG---'
curl -k -I -sS https://rgavanp.kdns.fr/blog/
echo '---HTTP_CREATE---'
curl -k -I -sS https://rgavanp.kdns.fr/blog/create/
echo '---LOG_TAIL---'
docker logs --tail 40 my_site_prod_repo-web-1 2>&1
