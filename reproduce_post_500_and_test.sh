
set -e
URL='https://rgavanp.kdns.fr/blog/2026/7/2/there-is-nobody-here-anymore-the-silence-of-virtual-places/'
echo '=== CURL DETAIL ==='
curl -k -i -sS "$URL" | head -n 60 || true
echo '=== WEB LOG TAIL ==='
docker logs --tail 220 my_site_prod_repo-web-1 2>&1 | tail -n 220
echo '=== MINIMAL DJANGO CLIENT TEST ==='
docker exec my_site_prod_repo-web-1 python manage.py shell -c "from django.test import Client; c=Client(HTTP_HOST='rgavanp.kdns.fr'); r=c.get('/blog/2026/7/2/there-is-nobody-here-anymore-the-silence-of-virtual-places/'); print('status=', r.status_code); print('content_start=', r.content[:300])"
echo '=== BLOG TESTS ==='
docker exec my_site_prod_repo-web-1 python manage.py test blog -v 2
