
set -e
cd /var/www/my_site_prod_repo_new
echo '=== REPAIR OCEANS MP3 BY STRIPPING BAD PREFIX ==='
docker exec my_site_prod_repo-web-1 python manage.py shell -c "from pathlib import Path; from django.conf import settings; from blog.models import AudioPost
root=Path(settings.MEDIA_ROOT)
a=AudioPost.objects.get(pk=3)
old=root/a.audio_file.name
data=old.read_bytes()
start=-1
for i in range(0, min(len(data)-1, 2000000)):
    if data[i] == 0xff and (data[i+1] & 0xe0) == 0xe0:
        start=i
        break
print('old=', a.audio_file.name, 'size=', len(data), 'first_sync=', start)
new_name='audio/2026/06/22/oceans-deep-repaired.mp3'
new=root/new_name
new.parent.mkdir(parents=True, exist_ok=True)
if start <= 0:
    raise SystemExit('No MP3 sync frame found')
new.write_bytes(data[start:])
a.audio_file.name=new_name
a.save(update_fields=['audio_file','updated'] if hasattr(a,'updated') else ['audio_file'])
print('new=', new_name, 'size=', new.stat().st_size, 'head=', new.read_bytes()[:16].hex())"
echo '=== FILE CHECK ==='
file /var/www/my_site_prod_repo_new/media/audio/2026/06/22/oceans-deep-repaired.mp3 || true
echo '=== PAGE SOURCES ==='
curl -k -sS https://rgavanp.kdns.fr/blog/audio/list/ | grep -E 'card-title|source src' || true
echo '=== VERIFY ALL AUDIO URLS ==='
docker exec my_site_prod_repo-web-1 python manage.py shell -c "from blog.models import AudioPost
for a in AudioPost.objects.order_by('id'): print(a.id, a.audio_file.url)" | awk '/^[0-9]/{print $1, $2}' | while read id url; do
  echo "--- $id $url"
  curl -k -sS -I -H 'Range: bytes=0-1023' "https://rgavanp.kdns.fr$url" | sed -n '1,14p'
done
