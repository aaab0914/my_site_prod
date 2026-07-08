# Test Index

This document lists the current test files in the project, their paths, and the recommended commands to run them.

Project root:

```powershell
cd G:\Projests\Python_Projects\my_site_prod-master
```

## CI Coverage

GitHub Actions now includes a Docker-based pipeline:

- builds the application image
- validates `docker-compose.yml`
- starts the Compose stack
- waits for the `web` health check
- runs `python manage.py test` inside the `web` container
- verifies `http://127.0.0.1/blog/` through `nginx`
- validates `docker-compose.prod.yml`

Workflow file:

```text
.github/workflows/docker-ci.yml
```

## Full Local Test Run

Run all Django tests inside the running Docker stack:

```powershell
docker compose up -d
docker compose exec web python manage.py test
```

## Application Tests

### Blog Tests

Package path:

```text
blog/tests/
```

Run:

```powershell
docker compose exec web python manage.py test blog.tests
```

Main coverage:

- blog routes
- post creation
- comment flows
- audio upload and audio list
- RSS feed
- search behavior
- admin blog actions
- API permission behavior
- Docker-related blog checks

Main module layout:

```text
blog/tests/test_blog/
  test_tags_and_feeds.py
  test_posts_and_comments.py
  test_audio.py
  test_api.py
  test_admin_and_docker.py
```

### Images Tests

Package path:

```text
images/tests/
```

Run:

```powershell
docker compose exec web python manage.py test images.tests
```

Main coverage:

- image app tests defined in `images/tests/test_images.py`

### Users Tests

Package path:

```text
users/tests/
```

Run:

```powershell
docker compose exec web python manage.py test users.tests
```

Main coverage:

- register
- login
- profile
- profile edit
- account delete
- username change
- user model behavior

Main module layout:

```text
users/tests/test_users/
  test_models.py
  test_auth.py
  test_profile.py
  test_account.py
```

## Project-Level Infrastructure Tests

### Docker Compose Tests

File path:

```text
my_site/tests/test_docker_compose.py
```

Run:

```powershell
docker compose exec web python manage.py test my_site.tests.test_docker_compose
```

Main coverage:

- `docker-compose.yml`
- `docker-compose.prod.yml`
- deploy scripts
- production compose usage rules
- production verification checklist existence

### Infrastructure Tests

Package path:

```text
my_site/tests/test_infrastructure/
```

Run:

```powershell
docker compose exec web python manage.py test my_site.tests.test_infrastructure
```

Main coverage:

- Gunicorn assumptions
- PostgreSQL compose configuration
- runtime probes
- entrypoint expectations
- permissions-related startup assumptions

Main module layout:

```text
my_site/tests/test_infrastructure/
  common.py
  test_nginx.py
  test_gunicorn.py
  test_postgres.py
  test_monitoring.py
  test_runtime_probes.py
```

### Nginx Config Tests

File path:

```text
my_site/tests/test_nginx_config.py
```

Run:

```powershell
docker compose exec web python manage.py test my_site.tests.test_nginx_config
```

Main coverage:

- `nginx.conf`
- reverse proxy behavior
- static and media routing

### Settings Tests

File path:

```text
my_site/tests/test_settings.py
```

Run:

```powershell
docker compose exec web python manage.py test my_site.tests.test_settings
```

Main coverage:

- settings split (`base/dev/prod`)
- logging policy
- upload limits
- dev/prod settings module selection

### Celery Integration Tests

File path:

```text
my_site/tests/test_celery_integration.py
```

Run:

```powershell
docker compose exec web python manage.py test my_site.tests.test_celery_integration
```

Main coverage:

- Celery worker and beat configuration
- eager task execution
- running worker inspect ping

### Sentry Integration Tests

File path:

```text
my_site/tests/test_sentry_integration.py
```

Run:

```powershell
docker compose exec web python manage.py test my_site.tests.test_sentry_integration
```

Main coverage:

- Django and Celery Sentry integration wiring
- Sentry init arguments
- exception capture paths

### Prometheus Integration Tests

File path:

```text
my_site/tests/test_prometheus_integration.py
```

Run:

```powershell
docker compose exec web python manage.py test my_site.tests.test_prometheus_integration
```

Main coverage:

- `/metrics` route
- Prometheus payload format
- Prometheus targets API
- target health for Django and celery-exporter

### Grafana Integration Tests

File path:

```text
my_site/tests/test_grafana_integration.py
```

Run:

```powershell
docker compose exec web python manage.py test my_site.tests.test_grafana_integration
```

Main coverage:

- datasource provisioning
- dashboard provisioning files
- Grafana health endpoint
- container-level dashboard file presence

## Useful Combined Runs

Run app behavior tests:

```powershell
docker compose exec web python manage.py test blog.tests images.tests users.tests
```

Run infrastructure and deployment tests:

```powershell
docker compose exec web python manage.py test my_site.tests.test_docker_compose my_site.tests.test_infrastructure my_site.tests.test_nginx_config my_site.tests.test_settings
```

Run observability integration tests:

```powershell
docker compose exec web python manage.py test my_site.tests.test_celery_integration my_site.tests.test_sentry_integration my_site.tests.test_prometheus_integration my_site.tests.test_grafana_integration
```

Run the currently most important stabilization set:

```powershell
docker compose exec web python manage.py test my_site.tests.test_settings my_site.tests.test_docker_compose blog.tests users.tests
```

## Current Test File List

```text
blog/tests/test_blog/test_tags_and_feeds.py
blog/tests/test_blog/test_posts_and_comments.py
blog/tests/test_blog/test_audio.py
blog/tests/test_blog/test_api.py
blog/tests/test_blog/test_admin_and_docker.py
images/tests/test_images.py
users/tests/test_users/test_models.py
users/tests/test_users/test_auth.py
users/tests/test_users/test_profile.py
users/tests/test_users/test_account.py
my_site/tests/test_docker_compose.py
my_site/tests/test_infrastructure/test_nginx.py
my_site/tests/test_infrastructure/test_gunicorn.py
my_site/tests/test_infrastructure/test_postgres.py
my_site/tests/test_infrastructure/test_monitoring.py
my_site/tests/test_infrastructure/test_runtime_probes.py
my_site/tests/test_nginx_config.py
my_site/tests/test_settings.py
my_site/tests/test_celery_integration.py
my_site/tests/test_sentry_integration.py
my_site/tests/test_prometheus_integration.py
my_site/tests/test_grafana_integration.py
```

## Notes

- The Docker-related runtime checks are most meaningful when the Compose stack is already running.
- Some tests still validate configuration invariants from repository files, but CI now also performs container build and startup verification instead of relying only on text assertions.
