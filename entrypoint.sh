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

mkdir -p "/code/logs/$(date +%Y-%m)"

# 自定义命令（如 celery worker/beat）以 app 用户身份运行
if [ "$#" -gt 0 ]; then
  exec gosu app "$@"
fi

ACCESS_PIPE="/tmp/gunicorn-access.pipe"
ERROR_PIPE="/tmp/gunicorn-error.pipe"
rm -f "$ACCESS_PIPE" "$ERROR_PIPE"
mkfifo "$ACCESS_PIPE"
mkfifo "$ERROR_PIPE"

python /code/scripts/runtime_log_router.py gunicorn_access < "$ACCESS_PIPE" &
python /code/scripts/runtime_log_router.py gunicorn_error < "$ERROR_PIPE" &

exec gosu app gunicorn \
  --workers ${GUNICORN_WORKERS:-2} \
  --worker-tmp-dir /dev/shm \
  --bind 0.0.0.0:8000 \
  --access-logfile "$ACCESS_PIPE" \
  --error-logfile "$ERROR_PIPE" \
  my_site.wsgi:application
