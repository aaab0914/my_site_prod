#!/bin/bash

set -e

COMPOSE_FILE="docker-compose.prod.yml"
APP_BASE_URL="${APP_BASE_URL:-http://localhost}"

print_logs_on_failure() {
    echo "Deployment failed. Recent container logs:"
    docker compose -f "${COMPOSE_FILE}" ps || true
    docker compose -f "${COMPOSE_FILE}" logs --tail=100 web nginx db || true
}

trap print_logs_on_failure ERR

wait_for_http() {
    local url="$1"
    local max_attempts="${2:-30}"
    local sleep_seconds="${3:-2}"
    local attempt=1

    while [ "${attempt}" -le "${max_attempts}" ]; do
        if curl -fsS "${url}" > /dev/null; then
            return 0
        fi

        echo "Waiting for ${url} (${attempt}/${max_attempts})..."
        sleep "${sleep_seconds}"
        attempt=$((attempt + 1))
    done

    echo "Timed out waiting for ${url}"
    return 1
}

echo "Starting production deployment with ${COMPOSE_FILE}..."

if ! docker info > /dev/null 2>&1; then
    echo "Docker is not running. Please start Docker first."
    exit 1
fi

docker compose -f "${COMPOSE_FILE}" up -d --build

echo "Waiting for services to initialize..."
sleep 10

docker compose -f "${COMPOSE_FILE}" exec -T web python manage.py check --deploy
docker compose -f "${COMPOSE_FILE}" exec -T web python manage.py migrate
docker compose -f "${COMPOSE_FILE}" exec -T web python manage.py collectstatic --noinput
docker compose -f "${COMPOSE_FILE}" exec -T db pg_isready -U "${DB_USER:-my_site_user}" -d "${DB_NAME:-my_site_db}"

wait_for_http "${APP_BASE_URL}/blog/"
curl -fsSI "${APP_BASE_URL}/users/login/" > /dev/null
curl -fsSI "${APP_BASE_URL}/blog/create/" > /dev/null

echo "Production service status:"
docker compose -f "${COMPOSE_FILE}" ps
echo "Production deployment verification passed."
