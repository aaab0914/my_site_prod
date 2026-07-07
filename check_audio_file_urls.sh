
set -e
echo '=== DB AUDIO URLS AND EXISTS ==='
docker exec my_site_prod_repo-web-1 python manage.py shell -c "from pathlib import Path; from django.conf import settings; from blog.models import AudioPost; root=Path(settings.MEDIA_ROOT)
for a in AudioPost.objects.all():
    print(a.id, a.audio_file.name, a.audio_file.url, (root/a.audio_file.name).exists())"
echo '=== CURL AUDIO URLS ==='
docker exec my_site_prod_repo-web-1 python manage.py shell -c "from blog.models import AudioPost
for a in AudioPost.objects.all(): print(a.audio_file.url)" | grep '^/media/' | while read url; do
  echo "--- $url"
  curl -k -I -sS "https://rgavanp.kdns.fr$url" | head -n 8 || true
done
