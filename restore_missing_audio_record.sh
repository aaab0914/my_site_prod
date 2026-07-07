
set -e
cd /var/www/my_site_prod_repo_new
echo '=== RESTORE MISSING AUDIOPOST ID 1 ==='
docker exec my_site_prod_repo-web-1 python manage.py shell -c "from pathlib import Path; from django.conf import settings; from django.contrib.auth import get_user_model; from blog.models import AudioPost
User=get_user_model()
user=User.objects.filter(id=1).first() or User.objects.filter(username='Ron_prod').first() or User.objects.first()
path='audio/2026/06/19/1-PRINCE_OF_DARKNESS-1080P_高清-AVC.mp3'
root=Path(settings.MEDIA_ROOT)
print('file_exists=', (root/path).exists(), root/path)
obj=AudioPost.objects.filter(audio_file=path).first()
if obj:
    print('already_exists=', obj.id, obj.music_name, obj.audio_file.name)
else:
    obj=AudioPost(id=1, music_name='11', audio_file=path, description='', uploaded_by=user)
    obj.save(force_insert=True)
    print('created=', obj.id, obj.music_name, obj.audio_file.name)
print('all_audio=', list(AudioPost.objects.order_by('id').values_list('id','music_name','audio_file')))
"
echo '=== FIX AUDIO SEQUENCE ==='
docker exec my_site_prod_repo-db-1 psql -U my_site_user -d my_site_db -c "SELECT setval(pg_get_serial_sequence('blog_audiopost','id'), COALESCE((SELECT MAX(id) FROM blog_audiopost), 1), true);"
echo '=== VERIFY AUDIO PAGE ==='
curl -k -sS https://rgavanp.kdns.fr/blog/audio/list/ | grep -E 'card-title|source src' || true
echo '=== VERIFY RESTORED AUDIO URL ==='
curl -k -I -sS 'https://rgavanp.kdns.fr/media/audio/2026/06/19/1-PRINCE_OF_DARKNESS-1080P_%E9%AB%98%E6%B8%85-AVC.mp3' | head -n 10 || true
echo '=== VERIFY ALL DB MEDIA HTTP ==='
docker exec my_site_prod_repo-web-1 python manage.py shell -c "from blog.models import Post,AudioPost
for url in [x.cover_image.url for x in Post.objects.exclude(cover_image='')] + [x.audio_file.url for x in AudioPost.objects.exclude(audio_file='')]: print(url)" | grep '^/media/' | while read url; do
  code=$(curl -k -o /dev/null -sS -w '%{http_code}' "https://rgavanp.kdns.fr$url" || true)
  echo "$code $url"
done
