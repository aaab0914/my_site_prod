#!/bin/bash
set -e

echo "=== Deploying my_site production stack ==="

cd "$(dirname "$0")"

echo "1. Validating production environment..."
if [ ! -f .env.prod ]; then
  echo "ERROR: .env.prod not found. Create it from .env.example first."
  exit 1
fi

echo "2. Pulling latest images..."
docker compose -f docker-compose.prod.yml pull

echo "3. Building and starting core services..."
docker compose -f docker-compose.prod.yml up -d --build web db redis elasticsearch celery celery-beat

echo "4. Running database migrations..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py migrate --noinput

echo "5. Collecting static files..."
docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput

echo "6. Checking health..."
sleep 5
docker compose -f docker-compose.prod.yml ps

echo "=== Deployment complete ==="
echo "Optional: start monitoring stack with:"
echo "  docker compose -f docker-compose.prod.yml --profile optional up -d nginx flower prometheus grafana loki promtail celery-exporter"
