
set -e
cd /var/www/my_site_prod_repo_new
echo '=== BACKUP CURRENT MEDIA LIST ==='
find media -type f -printf '%P\n' | sort > /root/codex_backups/media_new_before_restore_$(date +%Y%m%d_%H%M%S).txt
mkdir -p media
echo '=== RSYNC OLD MEDIA INTO CURRENT ==='
echo "restore_media_files.sh: external project sync source removed; using only /var/www/my_site_prod_repo_new" >&2
chown -R messagebus:crontab /var/www/my_site_prod_repo_new/media || true
chmod -R u+rwX,go+rX /var/www/my_site_prod_repo_new/media
echo '=== CHECK DB REFERENCES EXIST ==='
docker exec my_site_prod_repo-web-1 python manage.py shell -c "from pathlib import Path; from django.conf import settings; from blog.models import Post, AudioPost
root=Path(settings.MEDIA_ROOT)
for p in Post.objects.exclude(cover_image=''):
    print('POST', p.id, p.cover_image.name, (root/p.cover_image.name).exists())
for a in AudioPost.objects.all():
    print('AUDIO', a.id, a.audio_file.name, (root/a.audio_file.name).exists())"
echo '=== FIND AUDIO FILES ==='
find /var/www/my_site_prod_repo_new/media/audio -type f -printf '%P %s\n' | sort
echo '=== TEST MEDIA URLS ==='
for rel in \
'posts/2026/06/24/pasted-cover-image_HduTZ0D.jpg' \
'posts/2026/06/24/pasted-cover-image_BHT01G4.jpg' \
'posts/2026/06/24/pasted-cover-image.jpg' \
'posts/2026/06/24/2025-05-26_213733.jpg' \
'audio/2026/06/22/Oceans_Deep_1.mp3' \
'audio/2026/06/22/Midnight_City-Pixel_Perfect.mp3'; do
  echo "--- /media/$rel"
  curl -k -I -sS "https://rgavanp.kdns.fr/media/$rel" | head -n 8 || true
done
echo '=== TEST PAGES ==='
curl -k -I -sS https://rgavanp.kdns.fr/blog/ | head -n 8 || true
curl -k -I -sS https://rgavanp.kdns.fr/blog/audio/ | head -n 8 || true
