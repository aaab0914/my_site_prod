# Integrations Guide

This project now includes the following infrastructure integrations:

- Celery worker, Celery Beat, and Flower
- Redis as Celery broker/result backend
- Prometheus metrics endpoint at `/metrics`
- Prometheus server on port `9090`
- Grafana on port `3000`
- Flower on port `5555`
- Sentry SDK integration via `SENTRY_DSN`
- Elasticsearch service plus `django-elasticsearch-dsl` document for blog posts

## Runtime Summary

- `web` exposes Django and `/metrics` on container port `8000`
- `nginx` publishes the app on host port `80`
- `celery` runs with `-E` so Flower and monitoring can inspect worker state
- `celery-beat` runs with `-E` and loads the project beat schedule
- `celery-exporter` publishes Prometheus metrics on `9540`
- `prometheus` scrapes `web:8000/metrics` and `celery-exporter:9540/metrics`
- `grafana` provisions the Prometheus datasource and the `App Observability` dashboard at startup
- `sentry_sdk` is initialized for both Django and Celery when `SENTRY_DSN` is set

Required environment variables:

- `REDIS_URL=redis://redis:6379/0`
- `CELERY_BROKER_URL=redis://redis:6379/0`
- `CELERY_RESULT_BACKEND=redis://redis:6379/0`
- `ELASTICSEARCH_URL=http://elasticsearch:9200`
- `SENTRY_DSN=`
- `SENTRY_TRACES_SAMPLE_RATE=0.0`
- `SENTRY_PROFILES_SAMPLE_RATE=0.0`

Useful commands:

- `docker compose up -d --build`
- `docker compose exec web python manage.py search_index --rebuild`
- `docker compose exec web python manage.py shell -c "from blog.tasks import ping_blog_task; print(ping_blog_task.delay().id)"`
- `docker compose exec celery celery -A my_site inspect ping`
- `docker compose exec web python manage.py test my_site.tests_celery_integration my_site.tests_sentry_integration my_site.tests_prometheus_integration my_site.tests_grafana_integration`

Service URLs:

- Django app: `http://127.0.0.1/blog/`
- Prometheus: `http://127.0.0.1:9090`
- Grafana: `http://127.0.0.1:3000`
- Flower: `http://127.0.0.1:5555`
- Elasticsearch: `http://127.0.0.1:9200`

## Verification Steps

1. Start the stack:

```bash
docker compose up -d --build
```

2. Confirm service state:

```bash
docker compose ps
```

3. Confirm Django and exporter metrics:

```bash
curl http://localhost/metrics
curl http://localhost:9540/metrics
```

4. Confirm Prometheus targets:

```bash
curl http://localhost:9090/api/v1/targets
```

Expected result:
- `django` target health is `up`
- `celery-exporter` target health is `up`

5. Confirm Grafana health:

```bash
curl http://localhost:3000/api/health
```

6. Confirm Celery worker control path:

```bash
docker compose exec celery celery -A my_site inspect ping
```

7. Run observability regression tests:

```bash
docker compose exec web python manage.py test my_site.tests_celery_integration my_site.tests_sentry_integration my_site.tests_prometheus_integration my_site.tests_grafana_integration
```

## Common Failure Modes

### `/blog/` returns `502` after rebuilding `web`

Cause:
- `nginx` may still hold the old upstream container address after `web` is recreated

Recovery:

```bash
docker compose restart nginx
curl http://localhost/blog/
```

### Prometheus shows `django` target `down`

Check:

```bash
docker compose logs --tail=100 web
curl http://localhost:9090/api/v1/targets
```

Typical causes:
- Django rejects the internal host header with `DisallowedHost`
- `web` was recreated and Prometheus needs a fresh scrape cycle or restart

### Flower opens but shows inspect warnings

Check:

```bash
docker compose exec celery celery -A my_site inspect ping
docker compose logs --tail=100 flower
```

Expected:
- worker command includes `-E`
- `inspect ping` returns `pong`
