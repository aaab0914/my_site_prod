
set -e
cd /var/www/my_site_prod_repo_new
echo '=== CURRENT IMAGEPOST/AUDIOPOST ==='
docker exec my_site_prod_repo-web-1 python manage.py shell -c "from images.models import ImagePost; from blog.models import AudioPost; print('ImagePost count', ImagePost.objects.count()); print(list(ImagePost.objects.values_list('id','title','image')[:50])); print('AudioPost count', AudioPost.objects.count()); print(list(AudioPost.objects.values_list('id','music_name','audio_file')[:50]))"
echo '=== OLD DB BACKUPS TABLE DATA SEARCH ==='
for db in /var/www/my_site_prod_repo_new/backups/db/*.sql /var/www/my_site_prod_repo_new/backups/db/*.sql.gz /root/backups/database/*.sql.gz; do
  [ -f "$db" ] || continue
  echo "--- $db image/audio tables"
  zgrep -nE 'COPY (public\.)?(blog_audiopost|images_imagepost)|audio/|posts/.+\.(jpg|png|webp)' "$db" | head -n 120 || true
done
echo '=== ORPHAN MEDIA NOT DB REFERENCED ==='
docker exec my_site_prod_repo-web-1 python manage.py shell -c "from pathlib import Path; from django.conf import settings; from django.apps import apps; from django.db.models.fields.files import FileField; root=Path(settings.MEDIA_ROOT); refs=set()
for model in apps.get_models():
    for f in model._meta.fields:
        if isinstance(f, FileField):
            for obj in model.objects.all():
                name=getattr(getattr(obj,f.name),'name','') or ''
                if name: refs.add(name)
all_files=[str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()]
orphans=[p for p in all_files if p not in refs]
print('refs', len(refs), 'files', len(all_files), 'orphans', len(orphans))
for p in orphans[:200]: print(p)"
