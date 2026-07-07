#!/bin/sh
set -eu

echo "[$(date '+%Y-%m-%d %H:%M:%S')] backup_loop.sh disabled: backups are handled by host cron via /var/www/my_site_prod_repo_new/backup_db.sh"
while true; do
    sleep 259200
done
