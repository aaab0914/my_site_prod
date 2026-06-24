#!/bin/sh
set -e

chown -R app:app /code 2>/dev/null || true
chmod -R 755 /code/media /code/logs 2>/dev/null || true

python manage.py check --deploy 2>/dev/null || true
python manage.py collectstatic --noinput 2>/dev/null || true

# 启动后台备份进程
chmod +x /code/backup_loop.sh
/code/backup_loop.sh >> /code/logs/backup.log 2>&1 &

exec gunicorn --workers 3 --bind 0.0.0.0:8000 my_site.wsgi:application