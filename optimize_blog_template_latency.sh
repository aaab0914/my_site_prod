
set -e
cd /var/www/my_site_prod_repo_new
cp blog/templates/blog/post/all_posts_list.html blog/templates/blog/post/all_posts_list.html.bak_opt_$(date +%Y%m%d_%H%M%S)
python3 - <<'PY'
from pathlib import Path
path = Path('blog/templates/blog/post/all_posts_list.html')
text = path.read_text(encoding='utf-8')
old = """                <p>
                    {{ post.body|markdown|safe|truncatechars_html:100 }}
                </p>
"""
new = """                <p>
                    {{ post.body|striptags|truncatechars:140 }}
                </p>
"""
if old not in text:
    raise SystemExit('Target snippet not found in template')
path.write_text(text.replace(old, new, 1), encoding='utf-8')
PY
docker compose -p my_site_prod_repo -f docker-compose.prod.yml up -d --build web
sleep 12
echo '=== DJANGO QUERY PROFILE ==='
docker exec my_site_prod_repo-web-1 python manage.py shell -c "import time; from django.test import Client; from django.db import connection, reset_queries; from django.conf import settings; settings.DEBUG=True; c=Client(HTTP_HOST='rgavanp.kdns.fr');
for path in ['/blog/']:
    reset_queries(); t=time.time(); r=c.get(path); dt=time.time()-t; print(path, 'status=', r.status_code, 'time=', round(dt,3), 'queries=', len(connection.queries));
    for q in sorted(connection.queries, key=lambda x: float(x.get('time',0)), reverse=True)[:6]: print('  ', q.get('time'), q.get('sql','')[:180])"
echo '=== ORIGIN CURL ==='
for i in 1 2 3; do curl -H 'Host: rgavanp.kdns.fr' -o /dev/null -sS -w "run=$i code=%{http_code} ttfb=%{time_starttransfer} total=%{time_total}\n" http://127.0.0.1/blog/; done
