
printf '=== ACCEPTED SSH SOURCES ===\n'
if [ -f /var/log/auth.log ]; then grep 'Accepted ' /var/log/auth.log | awk '{print $1,$2,$3,$9,$11}' | sort | uniq -c | sort -nr; fi
printf '\n=== FAILED SSH TOP SOURCES ===\n'
lastb 2>/dev/null | awk 'NF>=3 && $3 ~ /^[0-9]/ {print $3}' | sort | uniq -c | sort -nr | head -n 20
printf '\n=== FAIL2BAN STATUS ===\n'
fail2ban-client status 2>/dev/null || true
for jail in $(fail2ban-client status 2>/dev/null | sed -n 's/.*Jail list:[[:space:]]*//p' | tr ',' ' '); do echo "--- $jail"; fail2ban-client status "$jail" 2>/dev/null || true; done
printf '\n=== OPEN PORTS SHORT ===\n'
ss -tlnp | awk 'NR==1 || /LISTEN/ {print}'
printf '\n=== UFW NUMBERED ===\n'
ufw status numbered || true
printf '\n=== WEB BAD REQUEST COUNTS FROM DJANGO LOG ===\n'
docker logs --since 24h my_site_prod_repo-web-1 2>&1 | grep -Eo "Invalid HTTP_HOST header: '[^']+'|Not Found: [^ ]+|Forbidden|CSRF|Internal Server Error: [^ ]+" | sort | uniq -c | sort -nr | head -n 50
printf '\n=== WEB REMOTE IP TOP FROM GUNICORN ACCESS ===\n'
docker exec my_site_prod_repo-web-1 sh -lc "find /code/logs -type f -name '*access*' -mtime -2 -print -exec sh -c 'for f; do awk '{print \\$1}' \"\\$f\"; done' sh {} + 2>/dev/null | sort | uniq -c | sort -nr | head -n 30" || true
printf '\n=== PROJECT GIT STATUS ===\n'
cd /var/www/my_site_prod_repo_new && git status --short 2>/dev/null || true
printf '\n=== RECENT SHELL HISTORY TAIL ===\n'
tail -n 80 /root/.bash_history 2>/dev/null || true
