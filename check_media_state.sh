
set -e
cd /var/www/my_site_prod_repo_new
echo '=== MEDIA DIRS ==='
ls -la /var/www/my_site_prod_repo_new/media || true
find /var/www/my_site_prod_repo_new/media -maxdepth 4 -type f | sed -n '1,120p' || true
echo '=== CONTAINER MEDIA ==='
docker exec my_site_prod_repo-web-1 sh -lc "python manage.py shell -c \"from django.conf import settings; print('MEDIA_ROOT=', settings.MEDIA_ROOT); print('MEDIA_URL=', settings.MEDIA_URL); print('STATIC_ROOT=', settings.STATIC_ROOT);\"; ls -la /code/media; find /code/media -maxdepth 4 -type f | head -n 120"
echo '=== NGINX DEFAULT ==='
sed -n '1,120p' /etc/nginx/sites-enabled/default
echo '=== COMPOSE VOLUMES WEB ==='
sed -n '1,120p' docker-compose.prod.yml
echo '=== DB MEDIA FIELDS ==='
docker exec my_site_prod_repo-web-1 python manage.py shell -c "from blog.models import Post, AudioPost; print('posts with cover:', list(Post.objects.exclude(cover_image='').values_list('id','title','cover_image')[:30])); print('audio:', list(AudioPost.objects.values_list('id','music_name','audio_file')[:30]))"
echo '=== URL CHECKS ==='
curl -k -I -sS https://rgavanp.kdns.fr/media/  || true
