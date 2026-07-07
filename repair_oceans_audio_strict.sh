
set -e
cd /var/www/my_site_prod_repo_new
echo '=== REPAIR OCEANS WITH STRICT MP3 HEADER ==='
docker exec my_site_prod_repo-web-1 python manage.py shell -c "from pathlib import Path; from django.conf import settings; from blog.models import AudioPost
root=Path(settings.MEDIA_ROOT)
a=AudioPost.objects.get(pk=3)
orig=root/'audio/2026/06/22/Oceans_Deep_1.mp3'
data=orig.read_bytes()
def id3_size(d):
    if d[:3] != b'ID3': return 0
    b=d[6:10]
    return 10 + ((b[0]&0x7f)<<21) + ((b[1]&0x7f)<<14) + ((b[2]&0x7f)<<7) + (b[3]&0x7f)
def valid_header(d,i):
    if i+4 > len(d): return False
    b1,b2,b3,b4=d[i],d[i+1],d[i+2],d[i+3]
    if b1 != 0xff or (b2 & 0xe0) != 0xe0: return False
    version=(b2>>3)&3; layer=(b2>>1)&3; bitrate=(b3>>4)&15; sr=(b3>>2)&3
    return version != 1 and layer == 1 and bitrate not in (0,15) and sr != 3
start0=id3_size(data)
start=-1
for i in range(start0, min(len(data)-4, start0+2000000)):
    if valid_header(data,i):
        start=i; break
print('id3_size=', start0, 'strict_start=', start, 'header=', data[start:start+8].hex())
new_name='audio/2026/06/22/oceans-deep-browser-safe.mp3'
new=root/new_name
new.write_bytes(data[start:])
a.audio_file.name=new_name
a.save(update_fields=['audio_file','updated'] if hasattr(a,'updated') else ['audio_file'])
print('new=', new_name, 'size=', new.stat().st_size, 'head=', new.read_bytes()[:16].hex())"
echo '=== FILE CHECK ==='
file /var/www/my_site_prod_repo_new/media/audio/2026/06/22/oceans-deep-browser-safe.mp3 || true
echo '=== PAGE SOURCES ==='
curl -k -sS https://rgavanp.kdns.fr/blog/audio/list/ | grep -E 'card-title|source src' || true
echo '=== VERIFY ALL AUDIO URLS CLEAN ==='
docker exec my_site_prod_repo-web-1 python manage.py shell -c "from blog.models import AudioPost
for a in AudioPost.objects.order_by('id'): print(f'{a.id} {a.audio_file.url}')" | grep -E '^[0-9]+ ' | while read id url; do
  code=$(curl -k -o /dev/null -sS -w '%{http_code}' -H 'Range: bytes=0-1023' "https://rgavanp.kdns.fr$url" || true)
  echo "$code $id $url"
done
