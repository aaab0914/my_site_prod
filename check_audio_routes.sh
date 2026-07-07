
set -e
echo '=== AUDIO URLS ==='
docker exec my_site_prod_repo-web-1 sh -lc "grep -n 'audio' /code/blog/urls.py | head -n 80"
echo '=== REVERSE ==='
docker exec my_site_prod_repo-web-1 python manage.py shell -c "from django.urls import reverse; print(reverse('blog:audio_list')); print(reverse('blog:audio_upload'))"
echo '=== TEST POSSIBLE AUDIO PAGES ==='
for path in /blog/audio/ /blog/audio/list/ /blog/audios/ /blog/audio-list/ /blog/audio/list /audio/; do
  code=$(curl -k -o /dev/null -sS -w '%{http_code}' "https://rgavanp.kdns.fr$path" || true)
  echo "$code $path"
done
echo '=== AUDIO LIST HEAD ==='
url=$(docker exec my_site_prod_repo-web-1 python manage.py shell -c "from django.urls import reverse; print(reverse('blog:audio_list'))" | tail -n 1)
echo "URL=$url"
curl -k -sS "https://rgavanp.kdns.fr$url" | head -n 60
