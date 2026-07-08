#!/bin/sh
set -e

chown -R app:app /code 2>/dev/null || true
chmod -R 755 /code/media /code/logs 2>/dev/null || true

if [ "${DJANGO_SETTINGS_MODULE}" = "my_site.settings.prod" ]; then
  python /code/validate_prod_env.py
  python manage.py check --deploy
fi

python manage.py check
python manage.py collectstatic --noinput || echo "collectstatic failed; continuing startup" >&2

# Host cron handles database backups; skip in-container backup loop
echo "Host cron handles database backups; skipping in-container backup loop" >&2

MONTH_DIR="$(date +%Y-%m)"
DAY="$(date +%Y-%m-%d)"
mkdir -p "/code/logs/${MONTH_DIR}"

if [ "$#" -gt 0 ]; then
  exec "$@"
fi

exec gunicorn \
  --workers 2 \
  --bind 0.0.0.0:8000 \
  --access-logfile "/code/logs/${MONTH_DIR}/gunicorn-access-${DAY}.log" \
  --error-logfile "/code/logs/${MONTH_DIR}/gunicorn-error-${DAY}.log" \
  my_site.wsgi:application
