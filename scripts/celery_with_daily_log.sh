#!/bin/sh
set -e

log_key="$1"
shift

exec "$@" 2>&1 | python /code/scripts/runtime_log_router.py "$log_key"
