
set -e
cd /var/www/my_site_prod_repo_new
echo '=== ALL DB MEDIA REFS JSON ==='
docker exec my_site_prod_repo-web-1 python manage.py shell -c "import json; from pathlib import Path; from django.conf import settings; from blog.models import Post, AudioPost; root=Path(settings.MEDIA_ROOT); rows=[]
for p in Post.objects.exclude(cover_image='').order_by('id'):
    rows.append({'type':'post_cover','id':p.id,'title':p.title,'path':p.cover_image.name,'exists':(root/p.cover_image.name).exists(),'url':p.cover_image.url})
for a in AudioPost.objects.exclude(audio_file='').order_by('id'):
    rows.append({'type':'audio','id':a.id,'title':a.music_name,'path':a.audio_file.name,'exists':(root/a.audio_file.name).exists(),'url':a.audio_file.url})
print(json.dumps(rows, ensure_ascii=False, indent=2))"
echo '=== ALL CURRENT MEDIA FILES ==='
find /var/www/my_site_prod_repo_new/media -type f -printf '%s %p\n' | sort -nr | head -n 300
echo '=== ALL OLD MEDIA FILES ==='
for d in /var/www/my_site_prod_repo/media /var/www/my_site_prod/media /var/www/my_site_prod_backup_20260624/media; do
  [ -d "$d" ] && echo "--- $d" && find "$d" -type f -printf '%s %p\n' | sort -nr | head -n 300
done
echo '=== MEDIA BACKUP TAR CONTENTS ==='
for t in /var/www/my_site_prod/backups/media_*.tar.gz /var/www/my_site_prod_backup_20260624/backups/media_*.tar.gz; do
  [ -f "$t" ] && echo "--- $t" && tar -tzf "$t" | head -n 80
done
