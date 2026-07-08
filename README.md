# my_site_prod-master

## Overview

`my_site_prod-master` is a Docker-based Django content site with:

- blog posts
- comments
- audio uploads
- user profiles and account actions
- Celery background jobs
- Redis
- PostgreSQL
- Elasticsearch
- Nginx
- Prometheus
- Grafana
- Flower

The project is designed to run locally with `docker compose` and includes supporting operational scripts, backup scripts, and observability configuration.

Recent codebase cleanup moved large single-file modules into package directories for better maintenance. Blog and user `views`, `forms`, and `models` now live in package-style layouts, and larger test files were split into focused test modules.

## Stack

- Python 3.12
- Django 6.0.2
- PostgreSQL 16
- Redis 7
- Celery 5.5
- Flower 2.0
- Elasticsearch 8.14
- Nginx 1.25
- Prometheus
- Grafana
- Gunicorn

Key Python packages in use:

- `django-extensions`
- `django-markdownx`
- `django-taggit`
- `djangorestframework`
- `django-filter`
- `psycopg`
- `sentry-sdk`
- `django-elasticsearch-dsl`

## Project Layout

```text
my_site_prod-master/
├── blog/
├── users/
├── my_site/
├── grafana/
├── backups/
├── media/
├── static/
├── staticfiles/
├── Shell_Commands/
├── docker-compose.yml
├── docker-compose.prod.yml
├── Dockerfile
├── nginx.conf
├── prometheus.yml
├── manage.py
└── README.md
```

## Services

The main local `docker-compose.yml` starts these services:

- `db` - PostgreSQL
- `redis` - Redis broker / cache
- `elasticsearch` - search backend
- `web` - Django + Gunicorn
- `celery` - worker
- `celery-beat` - scheduler
- `flower` - Celery monitoring UI
- `prometheus` - metrics scraping
- `grafana` - dashboards
- `celery-exporter` - Celery metrics
- `nginx` - reverse proxy

## Main Features

- blog list and detail pages
- tag-based content
- comment system
- audio upload and listing
- user registration, login, and profile management
- Django admin
- audit logging
- Celery task processing
- observability endpoints for Prometheus / Grafana / Flower

## Environment

Copy the example file and adjust values for your environment:

```bash
cp .env.example .env
```

Important variables:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `ELASTICSEARCH_URL`

The project currently expects PostgreSQL to be available through the `db` service and Redis through the `redis` service.

## Local Startup

Start the full stack:

```bash
docker compose up --build -d
```

Check status:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs --tail=100 web
docker compose logs --tail=100 db
docker compose logs --tail=100 nginx
```

## Common Django Operations

Run migrations:

```bash
docker compose exec web python manage.py migrate
```

Collect static files:

```bash
docker compose exec -T web python manage.py collectstatic --noinput
```

Create a superuser:

```bash
docker compose exec web python manage.py createsuperuser
```

Open a Django shell:

```bash
docker compose exec web python manage.py shell
```

## Main Local Endpoints

- `http://localhost/`
- `http://localhost/blog/`
- `http://localhost/users/login/`
- `http://localhost/users/register/`
- `http://localhost:3000/` - Grafana
- `http://localhost:5555/` - Flower
- `http://localhost:9090/` - Prometheus
- `http://localhost:9200/` - Elasticsearch
- `http://localhost:9540/metrics` - celery-exporter

## Backup And Restore

Relevant files:

- `backup_db.sh`
- `backup_db.ps1`
- `backup_loop.sh`
- `restore_test.ps1`
- `backups/`

Manual backup examples:

```bash
bash ./backup_db.sh
```

```powershell
& ".\backup_db.ps1"
```

Restore a SQL dump:

```bash
docker compose exec -T db psql -U "$DB_USER" -d "$DB_NAME" < backups/db/your_backup.sql
```

## Operational Notes

- The local stack uses Docker named volumes for PostgreSQL.
- Do not mount raw PostgreSQL data directories from Windows paths into `/var/lib/postgresql/data`.
- `celery-beat` should run with `celery -A my_site beat -l info`.
- If `web` is healthy but routes fail, inspect `web`, `nginx`, and `db` logs together.

## Useful Files

- [DOCKER_GUIDE.md](./DOCKER_GUIDE.md)
- [PROJECT_OPERATIONS_GUIDE.md](./PROJECT_OPERATIONS_GUIDE.md)
- [PRODUCTION_VERIFICATION.md](./PRODUCTION_VERIFICATION.md)
- [OBSERVABILITY_RUNBOOK.md](./OBSERVABILITY_RUNBOOK.md)
- [PSQL_GUIDE.md](./PSQL_GUIDE.md)
- [TEST_INDEX.md](./TEST_INDEX.md)
- [SOURCE_STRUCTURE.md](./SOURCE_STRUCTURE.md)
- [RUNTIME_ARTIFACTS.md](./RUNTIME_ARTIFACTS.md)

## Command Reference

Additional command cheat sheets are available in the project root:

- [REDIS_COMMANDS.md](./REDIS_COMMANDS.md)
- [NGINX_COMMANDS.md](./NGINX_COMMANDS.md)
- [CELERY_COMMANDS.md](./CELERY_COMMANDS.md)
- [PSQL_COMMANDS.md](./PSQL_COMMANDS.md)

Shell-level Django examples are also available under:

- `Shell_Commands/`

## Production

For production-style deployment, use:

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

Validate production environment values before deployment:

```bash
python validate_prod_env.py
```

## Current Caveats

- Security-related Django warnings may still appear if local `.env` values are development-oriented.
- Elasticsearch, Prometheus, Grafana, and Flower are enabled in the main stack, so the full project is heavier than a minimal Django deployment.
- This repository contains both application code and operational tooling; treat it as an app-plus-infra workspace rather than a minimal Django sample.
