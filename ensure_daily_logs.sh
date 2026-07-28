#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
LOG_ROOT="$PROJECT_DIR/logs"
MONTH_DIR="$(date +"%Y-%m")"
DAY="$(date +"%Y-%m-%d")"

ensure_log() {
    log_type="$1"
    prefix="$2"
    target_dir="$LOG_ROOT/$log_type/$MONTH_DIR"
    target_file="$target_dir/$prefix-$DAY.log"
    mkdir -p "$target_dir"
    touch "$target_file"
}

ensure_linked_log() {
    log_type="$1"
    prefix="$2"
    stable_name="$3"
    target_dir="$LOG_ROOT/$log_type/$MONTH_DIR"
    target_file="$target_dir/$prefix-$DAY.log"
    stable_file="$LOG_ROOT/$log_type/$stable_name"
    relative_target="$MONTH_DIR/$prefix-$DAY.log"
    mkdir -p "$target_dir"
    touch "$target_file"
    ln -sfn "$relative_target" "$stable_file"
}

ensure_log django django
ensure_log django-error django-error
ensure_log celery celery
ensure_linked_log gunicorn-access gunicorn-access access.log
ensure_linked_log gunicorn-error gunicorn-error error.log
ensure_linked_log nginx-access nginx-access access.log
ensure_linked_log nginx-error nginx-error error.log
ensure_log backup backup

if command -v docker >/dev/null 2>&1; then
    if docker ps --format '{{.Names}}' | grep -qx 'my_site_prod_repo_new-nginx-1'; then
        docker exec my_site_prod_repo_new-nginx-1 nginx -s reopen >/dev/null 2>&1 || true
    fi

    if docker ps --format '{{.Names}}' | grep -qx 'my_site_prod_repo_new-web-1'; then
        docker exec my_site_prod_repo_new-web-1 sh -lc 'pid=$(cat /tmp/gunicorn.pid 2>/dev/null || true); [ -n "$pid" ] && kill -USR1 "$pid" >/dev/null 2>&1 || true'
    fi
fi
