#!/bin/sh
set -e

chown -R app:app /code 2>/dev/null || true
chmod -R 755 /code/logs 2>/dev/null || true

if [ "${DJANGO_SETTINGS_MODULE}" = "my_site.settings.prod" ]; then
  python /code/validate_prod_env.py
  python manage.py check --deploy
fi

python manage.py check
python manage.py collectstatic --noinput || echo "collectstatic failed; continuing startup" >&2

# Host cron handles database backups; skip in-container backup loop
echo "Host cron handles database backups; skipping in-container backup loop" >&2

MONTH_DIR="$(date +%Y-%m)"
mkdir -p "/code/logs/django/${MONTH_DIR}" "/code/logs/django-error/${MONTH_DIR}" "/code/logs/celery/${MONTH_DIR}" "/code/logs/gunicorn-access/${MONTH_DIR}" "/code/logs/gunicorn-error/${MONTH_DIR}" "/code/logs/nginx-access/${MONTH_DIR}" "/code/logs/nginx-error/${MONTH_DIR}" "/code/logs/backup/${MONTH_DIR}"
/bin/sh /code/ensure_daily_logs.sh

if [ "$#" -gt 0 ]; then
  exec "$@"
fi

exec gunicorn \
  --workers 2 \
  --bind 0.0.0.0:8000 \
  --pid /tmp/gunicorn.pid \
  --access-logfile "/code/logs/gunicorn-access/access.log" \
  --error-logfile "/code/logs/gunicorn-error/error.log" \
  my_site.wsgi:application
