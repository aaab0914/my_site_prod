
set -e
cd /var/www/my_site_prod_repo_new
echo '=== AUDIO DB ==='
docker exec my_site_prod_repo-web-1 python manage.py shell -c "from blog.models import AudioPost
for a in AudioPost.objects.order_by('id'):
    print(a.id, a.music_name, a.audio_file.name, a.audio_file.url)"
echo '=== FILE/MIME/HEADERS ==='
docker exec my_site_prod_repo-web-1 python manage.py shell -c "from pathlib import Path; from django.conf import settings; from blog.models import AudioPost
root=Path(settings.MEDIA_ROOT)
for a in AudioPost.objects.order_by('id'):
    p=root/a.audio_file.name
    print('---', a.id, a.music_name)
    print('path=', p)
    print('exists=', p.exists(), 'size=', p.stat().st_size if p.exists() else None)
    if p.exists(): print('head=', p.read_bytes()[:32].hex())"
for rel in \
'audio/2026/06/19/1-PRINCE_OF_DARKNESS-1080P_高清-AVC.mp3' \
'audio/2026/06/22/Palmbomen_-_Stock_Soulwax_Remix_截取版.mp3' \
'audio/2026/06/22/Oceans_Deep_1.mp3' \
'audio/2026/06/22/Midnight_City-Pixel_Perfect.mp3'; do
  file="/var/www/my_site_prod_repo_new/media/$rel"
  echo "--- file $rel"
  file "$file" || true
  if command -v ffprobe >/dev/null 2>&1; then ffprobe -v error -show_format -show_streams "$file" | sed -n '1,80p' || true; fi
done
echo '=== HTTP RANGE CHECK ==='
for url in \
'/media/audio/2026/06/19/1-PRINCE_OF_DARKNESS-1080P_%E9%AB%98%E6%B8%85-AVC.mp3' \
'/media/audio/2026/06/22/Palmbomen_-_Stock_Soulwax_Remix_%E6%88%AA%E5%8F%96%E7%89%88.mp3' \
'/media/audio/2026/06/22/Oceans_Deep_1.mp3' \
'/media/audio/2026/06/22/Midnight_City-Pixel_Perfect.mp3'; do
  echo "--- $url"
  curl -k -sS -I -H 'Range: bytes=0-1' "https://rgavanp.kdns.fr$url" | sed -n '1,20p'
done
