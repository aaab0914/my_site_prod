#!/bin/sh
set -e

chown -R app:app /code 2>/dev/null || true
chmod -R 755 /code/media /code/logs 2>/dev/null || true

if [ "${DJANGO_SETTINGS_MODULE}" = "my_site.settings.prod" ]; then
  python /code/validate_prod_env.py
fi

python manage.py check --deploy
python manage.py collectstatic --noinput

# 启动后台备份进程
if [ -f /code/backup_loop.sh ]; then
  chmod +x /code/backup_loop.sh
  /code/backup_loop.sh >> /code/logs/backup.log 2>&1 &
else
  echo "backup_loop.sh not found; skipping background backup loop" >&2
fi

MONTH_DIR="$(date +%Y-%m)"
DAY="$(date +%Y-%m-%d)"
mkdir -p "/code/logs/${MONTH_DIR}"

if [ "$#" -gt 0 ]; then
  exec "$@"
fi

exec gunicorn \
  --workers 3 \
  --bind 0.0.0.0:8000 \
  --access-logfile "/code/logs/${MONTH_DIR}/gunicorn-access-${DAY}.log" \
  --error-logfile "/code/logs/${MONTH_DIR}/gunicorn-error-${DAY}.log" \
  my_site.wsgi:application
