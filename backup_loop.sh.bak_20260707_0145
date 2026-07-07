#!/bin/sh
set -e

BACKUP_DIR="/code/backups/db"
mkdir -p "$BACKUP_DIR"

while true; do
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="$BACKUP_DIR/my_site_db_${TIMESTAMP}.sql"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始执行数据库备份。"
    if docker compose exec -T db sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' > "$BACKUP_FILE"; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 备份成功: $BACKUP_FILE"
        find "$BACKUP_DIR" -name "*.sql" -type f | sort -r | tail -n +8 | xargs rm -f 2>/dev/null || true
    else
        rm -f "$BACKUP_FILE"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 备份失败。" >&2
    fi
    sleep 259200
done
