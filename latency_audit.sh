
set -e
URLS='https://rgavanp.kdns.fr/ https://rgavanp.kdns.fr/blog/ https://rgavanp.kdns.fr/blog/audio/list/'
echo '=== EXTERNAL CURL TIMINGS ==='
for u in $URLS; do
  echo "--- $u"
  curl -k -o /dev/null -sS -w 'code=%{http_code} dns=%{time_namelookup} connect=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer} total=%{time_total} size=%{size_download}\n' "$u"
done

echo '=== ORIGIN CURL TIMINGS ON SERVER ==='
for u in http://127.0.0.1/ http://127.0.0.1/blog/ http://127.0.0.1/blog/audio/list/; do
  echo "--- $u"
  curl -H 'Host: rgavanp.kdns.fr' -o /dev/null -sS -w 'code=%{http_code} connect=%{time_connect} ttfb=%{time_starttransfer} total=%{time_total} size=%{size_download}\n' "$u"
done

echo '=== DIRECT DJANGO CURL ==='
for u in http://172.19.0.4:8000/ http://172.19.0.4:8000/blog/ http://172.19.0.4:8000/blog/audio/list/; do
  echo "--- $u"
  curl -H 'Host: rgavanp.kdns.fr' -H 'X-Forwarded-Proto: https' -o /dev/null -sS -w 'code=%{http_code} connect=%{time_connect} ttfb=%{time_starttransfer} total=%{time_total} size=%{size_download}\n' "$u"
done

echo '=== NGINX CONFIG ==='
sed -n '1,140p' /etc/nginx/sites-enabled/default

echo '=== GUNICORN / WEB LOG TAIL ==='
docker logs --tail 120 my_site_prod_repo-web-1 2>&1 | tail -n 120

echo '=== DB ACTIVITY ==='
docker exec my_site_prod_repo-db-1 psql -U my_site_user -d my_site_db -c "select now(); select pid, state, wait_event_type, wait_event, query_start, left(query,120) from pg_stat_activity where datname='my_site_db' order by query_start desc limit 15;"

echo '=== DJANGO PAGE QUERY COUNTS ==='
docker exec my_site_prod_repo-web-1 python manage.py shell -c "import time; from django.test import Client; from django.db import connection, reset_queries; from django.conf import settings; settings.DEBUG=True; c=Client(HTTP_HOST='rgavanp.kdns.fr');
for path in ['/', '/blog/', '/blog/audio/list/']:
    reset_queries(); t=time.time(); r=c.get(path); dt=time.time()-t; print(path, 'status=', r.status_code, 'time=', round(dt,3), 'queries=', len(connection.queries));
    for q in sorted(connection.queries, key=lambda x: float(x.get('time',0)), reverse=True)[:8]: print('  ', q.get('time'), q.get('sql','')[:180])"

echo '=== STATIC/MEDIA COUNTS ==='
find /var/www/my_site_prod_repo_new/staticfiles -type f | wc -l
find /var/www/my_site_prod_repo_new/media -type f | wc -l
