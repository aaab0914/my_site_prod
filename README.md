# my_site

A Django blog project with post publishing, tags, comments, audio upload, user accounts, PostgreSQL, and Docker deployment.

## Main Features

- Blog post publishing and detail pages
- Tag filtering and post search
- Comment creation and editing
- Audio upload and audio list pages
- User registration, login, profile, and account actions
- Django admin, sitemap, and RSS feed support
- Docker Compose deployment with PostgreSQL and Nginx
- Celery worker, Celery Beat, Flower, Prometheus, Grafana, and Sentry integration

## Project Structure

```text
my_site_prod-master/
├── blog/
├── users/
├── my_site/
├── static/
├── staticfiles/
├── media/
├── manage.py
├── Dockerfile
├── docker-compose.yml
├── nginx.conf
└── README.md
```

## Key Routes

### Navigation

- `/blog/` — blog homepage
- `/users/login/` — login page
- `/users/register/` — register page
- `/users/profile/` — current user profile
- `/admin/` — Django admin

### Blog

- `/blog/create/` — create a new post
- `/blog/search/` — search posts
- `/blog/feed/` — latest posts RSS feed
- `/blog/audio/upload/` — upload audio
- `/blog/audio/list/` — audio list
- `/sitemap.xml` — sitemap

## Navigation HTML

A simple project entry page is available at `index.html`.

If you want to use it as a landing page, you can serve it directly with Nginx or place it into your template flow later.

## Environment Variables

Create a `.env` file in the project root.

Docker Compose now reads the database settings from this `.env` file instead of hard-coded values inside `docker-compose.yml`.

Local development example:

```env
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost
DB_NAME=my_site_db
DB_USER=my_site_user
DB_PASSWORD=your-strong-password
DB_HOST=db
DB_PORT=5432
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_HSTS_SECONDS=0
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False
```

Production-safe example:

```env
SECRET_KEY=change-me
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
DB_NAME=my_site_db
DB_USER=my_site_user
DB_PASSWORD=change-me
DB_HOST=db
DB_PORT=5432
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
CSRF_COOKIE_HTTPONLY=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_REFERRER_POLICY=same-origin
SECURE_CROSS_ORIGIN_OPENER_POLICY=same-origin
```

Tracked template:

```bash
cp .env.example .env
```

Production validation:

```bash
python validate_prod_env.py
```

## Run with Docker Compose

```bash
docker compose up --build -d
```

Development compose keeps the source bind mount for local editing and is only for local development.

## Docker Mirror

If image pulls are slow, configure a registry mirror in Docker Desktop before running `docker compose up`.

Windows Docker Desktop:

1. Open Docker Desktop.
2. Go to `Settings` -> `Docker Engine`.
3. Merge the following JSON and click `Apply & Restart`.

```json
{
  "registry-mirrors": [
    "https://docker.1ms.run",
    "https://hub.rat.dev",
    "https://docker.m.daocloud.io"
  ]
}
```

Verify the mirror is active:

```bash
docker info
```

Look for `Registry Mirrors` in the output, then retry:

```bash
docker compose pull
docker compose up --build -d
```

Notes:

- Mirror availability can change. If one address is slow or unavailable, remove it and keep the others.
- This changes Docker's global pull behavior on this machine, not only this project.
- If you use a proxy or VPN, test both enabled and disabled because some mirrors may be blocked or slower depending on your route.

Server production deployment must use `docker-compose.prod.yml`.

Production compose:

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

Deployment scripts:

```bash
bash ./deploy-local.sh
bash ./deploy-prod.sh
```

Server verification checklist:

```bash
Get-Content ./PRODUCTION_VERIFICATION.md
```

Open the site:

- `http://localhost/blog/`
- `http://localhost/users/login/`
- `http://localhost/users/register/`

Observability endpoints:

- `http://localhost:3000/` - Grafana
- `http://localhost:5555/` - Flower
- `http://localhost:9090/` - Prometheus
- `http://localhost:9540/metrics` - celery-exporter
- `http://localhost/metrics` - Django Prometheus metrics through Nginx

## First Startup Order

Recommended first-time startup sequence for local development:

1. Create and verify the root `.env` file.
2. Build and start the containers:

```bash
docker compose up --build -d
```

3. Run database migrations:

```bash
docker compose exec web python manage.py migrate
```

4. Collect static files:

```bash
docker compose exec -T web python manage.py collectstatic --noinput
```

5. Create an admin user if needed:

```bash
docker compose exec web python manage.py createsuperuser
```

6. Verify the main routes:

```bash
curl http://localhost/blog/
curl http://localhost/users/login/
curl http://localhost/users/register/
```

7. Verify service status:

```bash
docker compose ps
docker compose logs --tail=100 web
docker compose logs --tail=100 nginx
docker compose logs --tail=100 db
```

Wait until `web` is healthy before treating the site as ready.

## Run Migrations

```bash
docker compose exec web python manage.py migrate
```

## Infrastructure Tests

Static infrastructure checks:

```bash
docker compose exec web python manage.py test my_site.tests_infrastructure
```

Docker Compose specific checks:

```bash
docker compose exec web python manage.py test my_site.tests_docker_compose
```

Nginx configuration checks:

```bash
docker compose exec web python manage.py test my_site.tests_nginx_config
```

Observability integration checks:

```bash
docker compose exec web python manage.py test my_site.tests_celery_integration my_site.tests_sentry_integration my_site.tests_prometheus_integration my_site.tests_grafana_integration
```

These tests validate:

- `nginx.conf` reverse proxy and static/media routing
- Gunicorn startup command and container entrypoint assumptions
- PostgreSQL Compose configuration and optional runtime probes
- `web` healthcheck and `nginx` startup ordering
- Celery runtime wiring and worker inspect responses
- Sentry SDK integration wiring for Django and Celery
- Prometheus metrics exposure and scrape target health
- Grafana provisioning files and health endpoint

Some runtime probe tests are skipped automatically when `docker`, `nginx`, `gunicorn`, or `psql` are not available in the current environment.

## Troubleshooting Commands

Common operational checks:

```bash
docker compose ps
docker compose logs --tail=100 web
docker compose logs --tail=100 nginx
docker compose logs --tail=100 db
```

Check Django status inside the container:

```bash
docker compose exec web python manage.py check
docker compose exec web python manage.py showmigrations
docker compose exec web python manage.py test my_site.tests_infrastructure
```

Check database connectivity:

```bash
docker compose exec -T db pg_isready -U "$DB_USER" -d "$DB_NAME"
docker compose exec -T db psql -U "$DB_USER" -d "$DB_NAME" -c "\dt"
```

Check application and proxy endpoints:

```bash
curl http://localhost/
curl http://localhost/blog/
curl http://localhost/users/login/
```

If `/blog/` returns `500`, inspect:

```bash
Get-ChildItem .\logs\*\*.log
Get-Content .\logs\$(Get-Date -Format yyyy-MM)\error-$(Get-Date -Format yyyy-MM-dd).log -Tail 100
Get-Content .\logs\$(Get-Date -Format yyyy-MM)\django-$(Get-Date -Format yyyy-MM-dd).log -Tail 100
```

If static or media files fail to load:

```bash
docker compose exec -T web python manage.py collectstatic --noinput
docker compose logs --tail=100 nginx
```

If the `web` container fails with `permission denied` for `entrypoint.sh`:

```bash
docker compose build web
docker compose up -d web
docker compose logs --tail=100 web
```

The project is configured to run the entrypoint from `/usr/local/bin/entrypoint.sh`, which avoids host permission mismatches caused by the `/code` bind mount.

If `/blog/` or another proxied route returns `502` after rebuilding or recreating `web`:

```bash
docker compose ps
docker compose logs --tail=100 nginx
docker compose logs --tail=100 web
docker compose restart nginx
curl http://localhost/blog/
```

This project currently uses a Compose service-name upstream for Nginx. After `web` is recreated, restarting `nginx` is the fastest recovery step if it still holds the old upstream container address.

## Backup And Restore

Current project backup behavior:

- Manual database backup script: `backup_db.sh`
- Manual database backup script for Windows PowerShell: `backup_db.ps1`
- Background periodic backup loop: `backup_loop.sh` runs `pg_dump` inside the `db` container and retains the most recent 7 backups
- Backup output directory: `backups/db/`
- Automatic loop interval: every 3 days
- Automatic retention: latest 7 SQL backups
- Restore drill script for Windows PowerShell: `restore_test.ps1`

Create a manual database backup:

```bash
bash ./backup_db.sh
```

Or from PowerShell:

```powershell
& ".\backup_db.ps1"
```

List available backups:

```bash
ls -lah backups/db
```

Restore a backup into the PostgreSQL container:

```bash
docker compose exec -T db psql -U "$DB_USER" -d "$DB_NAME" < backups/db/your_backup_file.sql
```

Recommended restore workflow:

1. Stop write activity to the site before restore.
2. Make a fresh backup of the current database first.
3. Restore the selected SQL file into `my_site_db`.
4. Verify key routes such as `/blog/` and `/users/login/`.
5. Inspect logs after restore.

Post-restore verification:

```bash
docker compose exec -T db psql -U "$DB_USER" -d "$DB_NAME" -c "\dt"
curl http://localhost/blog/
docker compose logs --tail=100 web
```

Run a restore drill:

```powershell
& ".\restore_test.ps1"
```

Restore drill result:

- Backup dump completed successfully from the live `my_site_db`
- Backup restored successfully into a temporary `my_site_restore_drill` database
- Temporary database was removed after verification

## Collect Static Files

```bash
docker compose exec -T web python manage.py collectstatic --noinput
```

## Production Deployment

Use this path on the server. Do not use plain `docker compose up` for production, because that targets the development compose file.

1. Verify the root `.env` file contains production values.
2. Validate production values before startup:

```bash
python validate_prod_env.py
```

3. Start services with the production compose file:

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

4. Run migrations:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

5. Collect static files:

```bash
docker compose -f docker-compose.prod.yml exec -T web python manage.py collectstatic --noinput
```

6. Verify service health:

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs --tail=100 web
docker compose -f docker-compose.prod.yml logs --tail=100 nginx
docker compose -f docker-compose.prod.yml logs --tail=100 db
```

You can also use:

```bash
bash ./deploy-prod.sh
```

After deployment, run through `PRODUCTION_VERIFICATION.md`.

## Production Notes

- Current configuration is suitable for HTTP deployment behind Nginx.
- HTTPS-related Django security switches should only be enabled after Nginx is configured with TLS.
- Before calling production HTTPS complete, verify port 443, certificate renewal, and HTTP to HTTPS redirects on the real server.
- Nginx serves `/static/` and `/media/` directly.
- PostgreSQL runs in the `db` service defined in both compose files.
- The container entrypoint is copied outside `/code` so server-side bind mounts do not break startup permissions.
- Use `docker-compose.yml` for development and `docker-compose.prod.yml` for production-style deployment.
- Do not commit the real `.env`; commit `.env.example` only.
- Do not commit local runtime directories such as `logs/`, `backups/`, `media/`, `staticfiles/`, `.idea/`, or `data/`.
- Login is rate-limited after repeated failures, and uploads are restricted by file type and size.
- CI now audits Python dependencies and runs a Trivy scan before passing.
- Use `python monitor_health.py` or `docker compose exec -T web python /code/monitor_health.py` for a basic `/blog/` and `/users/login/` probe.

## Development Notes

- Source CSS is in `static/`.
- Externally served static assets may come from `staticfiles/` after collection or manual sync, depending on the deployment flow.
- Audio upload requires login.
