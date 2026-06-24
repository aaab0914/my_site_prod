#!/bin/bash

# 定期备份脚本
BACKUP_DIR="/code/backups/db"
mkdir -p "$BACKUP_DIR"

while true; do
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="$BACKUP_DIR/my_site_db_${TIMESTAMP}.sql"

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 执行数据库备份..."

    pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > "$BACKUP_FILE" 2>/dev/null

    if [ $? -eq 0 ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✓ 备份成功: $BACKUP_FILE"
        # 保留最近7个备份
        find "$BACKUP_DIR" -name "*.sql" -type f | sort -r | tail -n +8 | xargs rm -f 2>/dev/null
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✗ 备份失败"
    fi

    # 等待3天（259200秒）
    sleep 259200
done
