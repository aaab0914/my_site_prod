#!/bin/sh
set -eu

PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export PATH

PROJECT_DIR="/var/www/my_site_prod_repo_new"
BACKUP_DIR="$PROJECT_DIR/backups/db"
LOG_FILE="$PROJECT_DIR/logs/backup.log"
LOCK_DIR="$PROJECT_DIR/.backup_db.lock"
DOCKER_BIN="/usr/bin/docker"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/my_site_db_${TIMESTAMP}.sql"

mkdir -p "$BACKUP_DIR" "$(dirname "$LOG_FILE")"

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$1" | tee -a "$LOG_FILE"
}

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    log "Skip backup: another backup process is already running"
    exit 0
fi
trap 'rmdir "$LOCK_DIR"' EXIT INT TERM

cd "$PROJECT_DIR"
log "Starting database backup to $BACKUP_FILE"

if "$DOCKER_BIN" compose exec -T db sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' > "$BACKUP_FILE"; then
    size=$(wc -c < "$BACKUP_FILE")
    log "Backup succeeded: $BACKUP_FILE (${size} bytes)"
    find "$BACKUP_DIR" -name '*.sql' -type f | sort -r | tail -n +8 | xargs rm -f 2>/dev/null || true
else
    rm -f "$BACKUP_FILE"
    log "Backup failed"
    exit 1
fi
