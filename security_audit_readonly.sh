
set -u
printf '=== TIME ===\n'
date
printf '\n=== HOSTNAME ===\n'
hostname
printf '\n=== UPTIME ===\n'
uptime
printf '\n=== AUTH RECENT FAILURES ===\n'
lastb -n 20 2>/dev/null || true
printf '\n=== AUTH LOG SSH/PASSWORD/SUDO TAIL ===\n'
if [ -f /var/log/auth.log ]; then grep -Ei 'failed|failure|invalid|accepted|sudo|session|authentication' /var/log/auth.log | tail -n 120; fi
printf '\n=== NGINX ACCESS SUSPICIOUS ===\n'
for f in /var/log/nginx/access.log /var/log/nginx/*access*.log; do [ -f "$f" ] && echo "--- $f" && grep -Ei 'wp-admin|wp-login|\.env|phpmyadmin|/admin|/xmlrpc|/vendor|/\.git|select.+from|union.+select|base64|/shell|cmd=|passwd|etc/passwd|\.php|SDK/webLanguage' "$f" | tail -n 120; done
printf '\n=== NGINX ERROR TAIL ===\n'
for f in /var/log/nginx/error.log /var/log/nginx/*error*.log; do [ -f "$f" ] && echo "--- $f" && tail -n 120 "$f"; done
printf '\n=== DJANGO WEB LOG TAIL ===\n'
docker logs --tail 300 my_site_prod_repo-web-1 2>&1 | grep -Ei 'error|warning|disallowed|forbidden|csrf|traceback|invalid|not found|internal server|failed|exception|\.env|wp-|php|SDK/webLanguage' | tail -n 180 || true
printf '\n=== DOCKER PS ===\n'
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'
printf '\n=== LISTENING PORTS ===\n'
ss -tulpn
printf '\n=== UFW STATUS ===\n'
ufw status verbose || true
printf '\n=== RECENT MODIFIED PROJECT FILES ===\n'
find /var/www/my_site_prod_repo_new -type f -mtime -3 -not -path '*/.git/*' -printf '%TY-%Tm-%Td %TH:%TM %p\n' 2>/dev/null | sort | tail -n 80
printf '\n=== WORLD WRITABLE FILES PROJECT ===\n'
find /var/www/my_site_prod_repo_new -xdev -type f -perm -0002 -printf '%m %u:%g %p\n' 2>/dev/null | head -n 80
printf '\n=== SUID FILES RECENT SYSTEM ===\n'
find / -xdev -perm -4000 -type f -printf '%TY-%Tm-%Td %TH:%TM %m %u:%g %p\n' 2>/dev/null | sort | tail -n 80
printf '\n=== CRON SYSTEM ===\n'
crontab -l 2>/dev/null || true
ls -la /etc/cron.d /etc/cron.daily /etc/cron.hourly 2>/dev/null || true
printf '\n=== PROCESSES TOP CPU ===\n'
ps aux --sort=-%cpu | head -n 30
printf '\n=== PROCESSES TOP MEM ===\n'
ps aux --sort=-%mem | head -n 30
