
set -e
cd /var/www/my_site_prod_repo_new
echo '=== SANITIZE NON-ASCII AUDIO FILENAMES ==='
docker exec my_site_prod_repo-web-1 python manage.py shell -c "from pathlib import Path; from django.conf import settings; from blog.models import AudioPost
root=Path(settings.MEDIA_ROOT)
renames={
  1: 'audio/2026/06/19/prince-of-darkness-1080p-hd-avc.mp3',
  4: 'audio/2026/06/22/palmbomen-stock-soulwax-remix-clip.mp3',
}
for pk,new_name in renames.items():
    a=AudioPost.objects.get(pk=pk)
    old=root/a.audio_file.name
    new=root/new_name
    new.parent.mkdir(parents=True, exist_ok=True)
    if not new.exists():
        new.write_bytes(old.read_bytes())
    old_name=a.audio_file.name
    a.audio_file.name=new_name
    a.save(update_fields=['audio_file','updated'] if hasattr(a,'updated') else ['audio_file'])
    print(pk, old_name, '->', new_name, 'exists', new.exists(), 'size', new.stat().st_size)
print('all_audio=', list(AudioPost.objects.order_by('id').values_list('id','music_name','audio_file')))"
echo '=== VERIFY PAGE SOURCES ==='
curl -k -sS https://rgavanp.kdns.fr/blog/audio/list/ | grep -E 'card-title|source src' || true
echo '=== VERIFY ALL AUDIO URLS RANGE ==='
docker exec my_site_prod_repo-web-1 python manage.py shell -c "from blog.models import AudioPost
for a in AudioPost.objects.order_by('id'): print(a.id, a.audio_file.url)" | grep '^[0-9]' | while read id url; do
  echo "--- $id $url"
  curl -k -sS -I -H 'Range: bytes=0-1023' "https://rgavanp.kdns.fr$url" | sed -n '1,18p'
done
echo '=== AUDIO FILE COMMAND ==='
for f in \
/var/www/my_site_prod_repo_new/media/audio/2026/06/19/prince-of-darkness-1080p-hd-avc.mp3 \
/var/www/my_site_prod_repo_new/media/audio/2026/06/22/palmbomen-stock-soulwax-remix-clip.mp3 \
/var/www/my_site_prod_repo_new/media/audio/2026/06/22/Oceans_Deep_1.mp3 \
/var/www/my_site_prod_repo_new/media/audio/2026/06/22/Midnight_City-Pixel_Perfect.mp3; do
  file "$f" || true
done
