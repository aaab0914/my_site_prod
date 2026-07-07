
set -e
cd /var/www/my_site_prod_repo_new
echo '=== FIND BAD SLUGS ==='
docker exec my_site_prod_repo-web-1 python manage.py shell -c "import re; from blog.models import Post; bad=[]
pattern=re.compile(r'[-a-zA-Z0-9_]+$')
for p in Post.objects.all().order_by('id'):
    if not p.slug or not pattern.fullmatch(p.slug):
        bad.append((p.id,p.title,p.slug,str(p.publish)))
print('bad_count=', len(bad))
for row in bad: print(row)"
echo '=== FIX BAD SLUGS ==='
docker exec my_site_prod_repo-web-1 python manage.py shell -c "import re; from blog.models import Post; fixed=[]
pattern=re.compile(r'[-a-zA-Z0-9_]+$')
for p in Post.objects.all().order_by('id'):
    if not p.slug or not pattern.fullmatch(p.slug):
        old=p.slug
        p.slug=''
        p.slug=p.build_slug()
        p.save(update_fields=['slug','updated'])
        fixed.append((p.id,p.title,old,p.slug))
print('fixed_count=', len(fixed))
for row in fixed: print(row)
remaining=[]
for p in Post.objects.all().order_by('id'):
    if not p.slug or not pattern.fullmatch(p.slug): remaining.append((p.id,p.title,p.slug))
print('remaining=', remaining)"
echo '=== VERIFY URLS ==='
curl -k -I -sS https://rgavanp.kdns.fr/blog/2026/7/2/post-20260702124526/ || true
curl -k -I -sS https://rgavanp.kdns.fr/blog/2026/7/2/there-is-nobody-here-anymore-the-silence-of-virtual-places/ || true
echo '=== DJANGO CLIENT VERIFY ==='
docker exec my_site_prod_repo-web-1 python manage.py shell -c "from django.test import Client; from blog.models import Post; c=Client(HTTP_HOST='rgavanp.kdns.fr');
for p in Post.published.all()[:10]:
    url=p.get_absolute_url()
    r=c.get(url)
    print(p.id, url, r.status_code)"
