# Observability Runbook

This runbook covers the project's Celery, Sentry, Prometheus, Grafana, and Flower operations.

## Service Map

- Django app: `http://localhost/blog/`
- Django metrics: `http://localhost/metrics`
- Flower: `http://localhost:5555/`
- Prometheus: `http://localhost:9090/`
- Grafana: `http://localhost:3000/`
- celery-exporter metrics: `http://localhost:9540/metrics`

## Start And Verify

```bash
docker compose up -d --build
docker compose ps
curl http://localhost/blog/
curl http://localhost/metrics
curl http://localhost:9540/metrics
curl http://localhost:9090/api/v1/targets
curl http://localhost:3000/api/health
docker compose exec celery celery -A my_site inspect ping
```

## Regression Tests

```bash
docker compose exec web python manage.py test my_site.tests_celery_integration my_site.tests_sentry_integration my_site.tests_prometheus_integration my_site.tests_grafana_integration
```

## Common Checks

Check logs:

```bash
docker compose logs --tail=100 web
docker compose logs --tail=100 nginx
docker compose logs --tail=100 celery
docker compose logs --tail=100 flower
docker compose logs --tail=100 prometheus
docker compose logs --tail=100 grafana
```

Check Prometheus target health:

```bash
curl http://localhost:9090/api/v1/targets
```

Check Celery worker control path:

```bash
docker compose exec celery celery -A my_site inspect ping
docker compose exec celery celery -A my_site status
```

## Failure Recovery

### `/blog/` returns `502`

Typical cause:
- `web` was recreated and `nginx` still points to the old upstream container address

Recovery:

```bash
docker compose ps
docker compose logs --tail=100 nginx
docker compose logs --tail=100 web
docker compose restart nginx
curl http://localhost/blog/
```

### Prometheus `django` target is `down`

Checks:

```bash
curl http://localhost:9090/api/v1/targets
docker compose logs --tail=100 web
docker compose logs --tail=100 prometheus
```

Recovery:

```bash
docker compose restart prometheus
curl http://localhost:9090/api/v1/targets
```

If Django logs show `DisallowedHost`, confirm the container runtime `ALLOWED_HOSTS` includes internal Docker names such as `web`.

### Flower opens but has no worker data

Checks:

```bash
docker compose exec celery celery -A my_site inspect ping
docker compose logs --tail=100 flower
docker compose logs --tail=100 celery
```

Expected:
- Celery worker command includes `-E`
- `inspect ping` returns `pong`

### Grafana is up but dashboards are missing

Checks:

```bash
docker compose exec grafana sh -c "ls -R /etc/grafana/provisioning/dashboards"
curl http://localhost:3000/api/health
docker compose logs --tail=100 grafana
```

Recovery:

```bash
docker compose restart grafana
```

### Sentry appears inactive

Checks:

```bash
docker compose exec web python manage.py shell -c "from django.conf import settings; print(bool(settings.SENTRY_DSN))"
docker compose exec celery python -c "from django.conf import settings; print(bool(settings.SENTRY_DSN))"
```

Confirm `.env` contains:

```env
SENTRY_DSN=
SENTRY_TRACES_SAMPLE_RATE=0.0
SENTRY_PROFILES_SAMPLE_RATE=0.0
```

## Recommended Operator Sequence After Config Changes

1. Rebuild affected services.
2. If `web` was recreated, restart `nginx`.
3. If metrics wiring changed, restart `prometheus`.
4. Re-run observability integration tests.
5. Recheck `/blog/`, `/metrics`, Prometheus targets, and Grafana health.
