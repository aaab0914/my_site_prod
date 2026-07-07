
set -e
cd /var/www/my_site_prod_repo_new
echo '=== TOOL CHECK ==='
for t in ffmpeg ffprobe lame mpg123 sox python3; do command -v $t || true; done
echo '=== MP3 FRAME SCAN ==='
docker exec my_site_prod_repo-web-1 python manage.py shell -c "from pathlib import Path; from django.conf import settings; from blog.models import AudioPost
root=Path(settings.MEDIA_ROOT)
def id3_size(data):
    if data[:3] != b'ID3': return 0
    s=data[6:10]
    return 10 + ((s[0]&0x7f)<<21) + ((s[1]&0x7f)<<14) + ((s[2]&0x7f)<<7) + (s[3]&0x7f)
def find_sync(data, start=0):
    for i in range(start, min(len(data)-1, start+2000000)):
        if data[i] == 0xff and (data[i+1] & 0xe0) == 0xe0:
            return i
    return -1
for a in AudioPost.objects.order_by('id'):
    p=root/a.audio_file.name; data=p.read_bytes(); skip=id3_size(data); sync=find_sync(data, skip)
    print(a.id, a.music_name, 'size', len(data), 'id3_skip', skip, 'first_sync', sync, 'bytes_at_sync', data[sync:sync+8].hex() if sync>=0 else None)"
echo '=== TRY FFMPEG PROBE IF AVAILABLE ==='
if command -v ffprobe >/dev/null 2>&1; then
  for f in /var/www/my_site_prod_repo_new/media/audio/2026/06/*/*.mp3; do echo "--- $f"; ffprobe -hide_banner "$f" 2>&1 | head -n 40 || true; done
else
  echo 'ffprobe not installed on host'
fi
