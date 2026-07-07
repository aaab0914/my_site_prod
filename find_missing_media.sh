
set -e
echo '=== SEARCH REFERENCED MEDIA ==='
for rel in \
'posts/2026/06/24/pasted-cover-image_HduTZ0D.jpg' \
'posts/2026/06/24/pasted-cover-image_BHT01G4.jpg' \
'posts/2026/06/24/pasted-cover-image.jpg' \
'posts/2026/06/24/2025-05-26_213733.jpg' \
'audio/2026/06/22/Palmbomen_-_Stock_Soulwax_Remix_截取版.mp3' \
'audio/2026/06/22/Oceans_Deep_1.mp3' \
'audio/2026/06/22/Midnight_City-Pixel_Perfect.mp3'; do
  echo "--- $rel"
  find /root /var/www /var/lib/docker/volumes -path "*/$rel" -type f -printf '%s %p\n' 2>/dev/null | head -n 20 || true
done
echo '=== MEDIA TREES ==='
for d in /var/www/my_site_prod/media /var/www/my_site_prod_repo/media /var/www/my_site_prod_backup_20260624/media /root/media /root/backups /var/www/my_site_prod_repo_new/media; do
  [ -d "$d" ] && echo "--- $d" && find "$d" -maxdepth 5 -type f -printf '%s %p\n' | head -n 80
done
echo '=== BACKUP ARCHIVES ==='
find /root /var/www -maxdepth 5 \( -name '*.tar' -o -name '*.tar.gz' -o -name '*.zip' -o -name '*.sql.gz' \) -printf '%TY-%Tm-%Td %TH:%TM %s %p\n' 2>/dev/null | sort | tail -n 80
