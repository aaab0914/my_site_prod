# Production Verification

This checklist is for real server verification after deploying with `docker-compose.prod.yml`.

## Rule

Use the production compose file for all server operations:

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

Do not use plain `docker compose up` on the server.

## Startup Verification

1. Confirm containers are up:

```bash
docker compose -f docker-compose.prod.yml ps
```

2. Check recent logs:

```bash
docker compose -f docker-compose.prod.yml logs --tail=100 web
docker compose -f docker-compose.prod.yml logs --tail=100 nginx
docker compose -f docker-compose.prod.yml logs --tail=100 db
docker compose -f docker-compose.prod.yml logs --tail=100 prometheus
docker compose -f docker-compose.prod.yml logs --tail=100 grafana
```

3. Confirm database readiness:

```bash
docker compose -f docker-compose.prod.yml exec db pg_isready -U "$DB_USER" -d "$DB_NAME"
```

4. Confirm migrations:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py showmigrations
```

5. Confirm Django deploy checks:

```bash
docker compose -f docker-compose.prod.yml exec -T web python manage.py check --deploy
```

## Route Verification

Verify these routes from the server:

```bash
curl http://localhost/blog/
curl -I http://localhost/blog/create/
curl http://localhost/blog/audio/list/
curl -I http://localhost/users/login/
```

Expected behavior:

- `/blog/` returns `200`
- `/blog/create/` redirects anonymous users to login or returns the expected protected response
- `/blog/audio/list/` returns `200`
- `/users/login/` returns `200`

## Monitoring Verification

Verify these endpoints from the server:

```bash
curl http://localhost/metrics
curl http://localhost:9540/metrics
curl http://localhost:9090/api/v1/targets
curl http://localhost:3000/api/health
```

Expected behavior:

- `/metrics` returns `200`
- `:9540/metrics` returns `200`
- Prometheus target list shows `django` and `celery-exporter` as `up`
- Grafana health returns `database":"ok"`

Verify Celery control and worker visibility:

```bash
docker compose -f docker-compose.prod.yml exec celery celery -A my_site inspect ping
docker compose -f docker-compose.prod.yml logs --tail=100 flower
```

## Static And Media Verification

1. Re-run static collection if needed:

```bash
docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput
```

2. Confirm Nginx serves static and media paths without upstream errors.

## Post-Deploy Data Safety Verification

1. Take a fresh backup.
2. Confirm the backup file exists.
3. Keep one recent restore drill result recorded with date and target database name.

## Incident Checks

If Nginx shows `502 Bad Gateway` right after startup:

- wait for `web` health to turn healthy
- re-check `docker compose -f docker-compose.prod.yml ps`
- inspect `web` logs before restarting anything

If Nginx shows `502 Bad Gateway` after `web` was rebuilt or recreated:

```bash
docker compose -f docker-compose.prod.yml restart nginx
curl http://localhost/blog/
```

If Prometheus shows the `django` target as `down`:

```bash
docker compose -f docker-compose.prod.yml logs --tail=100 web
docker compose -f docker-compose.prod.yml restart prometheus
curl http://localhost:9090/api/v1/targets
```
