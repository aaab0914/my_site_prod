#!/bin/sh

BACKUP_DIR="./backups/db"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/my_site_db_${TIMESTAMP}.sql"

echo "[$(date)] 开始备份数据库..."

if docker compose exec -T db sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' > "$BACKUP_FILE"; then
    echo "[$(date)] ✓ 备份成功: $BACKUP_FILE"
    find "$BACKUP_DIR" -name "*.sql" -type f | sort -r | tail -n +8 | xargs rm -f 2>/dev/null
else
    rm -f "$BACKUP_FILE"
    echo "[$(date)] ✗ 备份失败"
    exit 1
fi
