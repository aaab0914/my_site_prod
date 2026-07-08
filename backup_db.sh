#!/bin/sh
set -eu

PROJECT_DIR="/var/www/my_site_prod_repo_new"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"
PROJECT_NAME="my_site_prod_repo"
BACKUP_DIR="$PROJECT_DIR/backups/db"
LOG_DIR="$PROJECT_DIR/logs"
RETENTION_COUNT="${RETENTION_COUNT:-7}"
MIN_INTERVAL_SECONDS="${MIN_INTERVAL_SECONDS:-0}"
FORCE_BACKUP="${FORCE_BACKUP:-0}"

mkdir -p "$BACKUP_DIR" "$LOG_DIR"

latest_backup="$(find "$BACKUP_DIR" -maxdepth 1 -type f -name 'my_site_db_*.sql' | sort -r | head -n 1 || true)"
if [ "$FORCE_BACKUP" != "1" ] && [ -n "$latest_backup" ]; then
    now_ts=$(date +%s)
    last_ts=$(stat -c %Y "$latest_backup")
    age=$((now_ts - last_ts))
    if [ "$age" -lt "$MIN_INTERVAL_SECONDS" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Skip backup: latest backup is ${age}s old (< ${MIN_INTERVAL_SECONDS}s): $latest_backup"
        exit 0
    fi
fi

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/my_site_db_${TIMESTAMP}.sql"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting database backup to $BACKUP_FILE"
if docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" exec -T db sh -lc 'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' > "$BACKUP_FILE"; then
    size=$(stat -c %s "$BACKUP_FILE")
    if [ "$size" -le 0 ]; then
        rm -f "$BACKUP_FILE"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup failed: output file is empty" >&2
        exit 1
    fi
    find "$BACKUP_DIR" -maxdepth 1 -type f -name 'my_site_db_*.sql' | sort -r | tail -n +$((RETENTION_COUNT + 1)) | xargs -r rm -f
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup succeeded: $BACKUP_FILE (${size} bytes)"
else
    rm -f "$BACKUP_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backup failed during pg_dump" >&2
    exit 1
fi
