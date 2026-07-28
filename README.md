# My Site - Django Blog and Media Platform

> A Docker-based Django platform for blogging, image galleries, albums, audio publishing, video publishing, protected media delivery, user profiles, API access, search, background jobs, and operations tooling.

## Current Feature Set

### Blog
- Create, edit, publish, and delete posts
- Markdown-based post authoring
- Automatic slug generation and unique publish-date constraints
- Tag support with normalized display rules
- Blog search with sorting and pagination
- RSS feeds for global and per-user content
- Comment creation, editing, and deletion
- Profile-linked author browsing
- Operation success flows after create and upload actions

### Media
- Gallery uploads with list, detail, edit, and delete pages
- Album uploads where one batch creates one album
- Album detail, edit, and delete pages
- Audio uploads with:
  - multi-file upload support
  - list pagination
  - per-track loop toggle
  - single-active-player behavior
  - edit and delete pages
  - optional cover image editing
- Video uploads and management for privileged users
- Public video list page
- Protected media proxy routes so storage paths are not exposed in normal UI
- Unified media naming and directory separation for images, gallery, albums, audio, comments, posts, and videos
- Deleted media moves to `.trash` instead of immediate permanent removal

### Accounts and Profiles
- Registration, login, logout, and account deletion
- Profile editing with avatar, bio, and location
- Profile page sections for:
  - paginated posts
  - comments
  - gallery uploads
  - albums
  - audio uploads
  - video uploads
- Administrator badge for superusers
- Avatar change cooldown support
- Token generation page for authenticated users
- Token regeneration cooldown for regular users with replacement of old tokens

### API and Guides
- Token-authenticated API access
- Dedicated token issue flow at `/api/token/`
- Public API entry points for posts and related content
- Frontend API token page with copy-ready examples
- Separate Python API guide page
- Separate cURL API guide page
- Terminal and script-friendly publishing workflows

### Search, Sorting, and Browsing
- Search page with result counts, paging, and sort controls
- Search result inclusion for posts and additional media titles
- Blog ordering options such as newest, oldest, and title-based modes
- Gallery ordering support
- Centralized browsing flows from the landing portal page

### Caching and Background Work
- Redis-backed Django cache
- Media list caching for gallery, audio, and video pages
- Cache invalidation on media save/delete flows
- Browser cache headers for common media formats
- Celery worker and Celery Beat support
- Media maintenance helpers for cleaning broken references and orphan files

### Operations and Logging
- Docker Compose production stack
- PostgreSQL, Redis, Elasticsearch, Celery, Flower, Prometheus, Grafana, Loki, Promtail, and Nginx support
- Health checks in the production stack
- Audit logging and backup support
- Structured log directories for:
  - Django
  - Django error
  - Gunicorn access
  - Gunicorn error
  - Celery
  - Nginx access
  - Nginx error
- Portal landing page for quick access to public pages, account actions, API pages, and media areas

## Main Routes

### Public
- `/` - portal landing page
- `/blog/` - blog homepage
- `/blog/search/` - post search
- `/blog/audio/list/` - audio library
- `/blog/video/list/` - video library
- `/blog/gallery/` - gallery
- `/blog/album/` - albums
- `/api/guide/` - cURL API guide
- `/api/python-guide/` - Python API guide
- `/users/login/` - login
- `/users/register/` - register

### Authenticated
- `/blog/create/` - create post
- `/blog/audio/upload/` - upload audio
- `/blog/gallery/upload/` - upload one image
- `/blog/album/upload/` - upload one album batch
- `/users/profile/` - profile page
- `/users/profile_edit/` - edit profile
- `/users/api-token/` - token management page
- `/operation/success/` - success page flow target

### Privileged
- `/blog/video/upload/` - upload video
- `/blog/video/<id>/` - video detail
- `/blog/video/<id>/edit/` - video edit
- `/blog/video/<id>/delete/` - video delete
- `/secure-console-7f9a2c-admin/` - Django admin

## Production Stack

Core services:
- `web`
- `db`
- `redis`
- `elasticsearch`
- `celery`
- `celery-beat`
- `nginx`

Operations and observability services:
- `flower`
- `prometheus`
- `grafana`
- `loki`
- `promtail`
- `celery-exporter`

## Quick Start

### Requirements
- Docker
- Docker Compose plugin

### Local Development

1. Enter the project directory
```bash
cd /path/to/my_site_prod-master
```

2. Prepare the local environment file
```bash
cp .env.dev .env.dev.local
```

3. Start the local stack
```bash
docker compose up -d --build
```

4. Run migrations
```bash
docker compose exec web python manage.py migrate
```

5. Create a superuser
```bash
docker compose exec web python manage.py createsuperuser
```

### Production Deployment

1. Enter the project directory on the target server
```bash
cd /var/www/my_site_prod_repo_new
```

2. Prepare the production environment file
Edit `.env.prod` and replace placeholder secrets before startup:
- `SECRET_KEY`
- `DB_PASSWORD`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `ELASTICSEARCH_URL`
- `PROMETHEUS_EXTERNAL_URL`
- `GRAFANA_ROOT_URL`

3. Start the main production services
```bash
docker compose -f docker-compose.prod.yml up -d --build web db redis elasticsearch celery celery-beat nginx
```

4. Run migrations
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

5. Create a superuser
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### Optional Operations Stack
```bash
docker compose -f docker-compose.prod.yml up -d flower prometheus grafana loki promtail celery-exporter
```

## Useful Commands

Rebuild application services:
```bash
docker compose -f docker-compose.prod.yml up -d --build web celery celery-beat nginx
```

Run tests:
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py test
```

Run deployment checks:
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py check --deploy
```

Check current service state:
```bash
docker compose -f docker-compose.prod.yml ps
docker stats --no-stream
```

## Project Structure

```text
my_site_prod_repo_new/
|- blog/                    # Posts, comments, audio, video, feeds, API
|- users/                   # Authentication, profile, avatar, token controls
|- images/                  # Gallery and album features
|- my_site/                 # Settings, URLs, middleware, media helpers, runtime helpers
|- media/                   # Uploaded files
|- staticfiles/             # Collected static assets
|- logs/                    # Runtime logs grouped by service
|- grafana/                 # Grafana provisioning
|- loki/                    # Loki configuration
|- promtail/                # Promtail configuration
|- backups/                 # Backup files
|- .env.prod                # Production environment file
|- docker-compose.prod.yml  # Production stack
|- Dockerfile
|- nginx.prod.conf
|- README.md
`- index.html               # Portal landing page
```
