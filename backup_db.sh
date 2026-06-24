#!/bin/bash

BACKUP_DIR="./backups/db"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/my_site_db_${TIMESTAMP}.sql"

echo "[$(date)] 开始备份数据库..."

docker-compose exec -T db pg_dump -U my_site_user -d my_site_db > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "[$(date)] ✓ 备份成功: $BACKUP_FILE"
    # 保留最近7个备份，删除旧的
    find "$BACKUP_DIR" -name "*.sql" -type f -mtime +7 -delete
else
    echo "[$(date)] ✗ 备份失败"
    exit 1
fi
