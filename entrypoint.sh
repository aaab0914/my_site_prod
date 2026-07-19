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

start_daily_log_router() {
  pipe_path="$1"
  prefix="$2"

  rm -f "$pipe_path"
  mkfifo "$pipe_path"

  (
    while IFS= read -r line || [ -n "$line" ]; do
      month_dir="/code/logs/$(date +%Y-%m)"
      day="$(date +%Y-%m-%d)"
      mkdir -p "$month_dir"
      printf '%s\n' "$line" >> "$month_dir/${prefix}-${day}.log"
    done < "$pipe_path"
  ) &
}

if [ "$#" -gt 0 ]; then
  exec "$@"
fi

ACCESS_PIPE="/tmp/gunicorn-access.pipe"
ERROR_PIPE="/tmp/gunicorn-error.pipe"
start_daily_log_router "$ACCESS_PIPE" "gunicorn-access"
start_daily_log_router "$ERROR_PIPE" "gunicorn-error"

exec gunicorn \
  --workers 2 \
  --bind 0.0.0.0:8000 \
  --access-logfile "$ACCESS_PIPE" \
  --error-logfile "$ERROR_PIPE" \
  my_site.wsgi:application
