# My Site - Django Blog and Media Platform

> A Docker-based Django platform for blogging, image galleries, albums, audio publishing, protected media delivery, user profiles, background jobs, and operations tooling.

## Current Feature Set

### Blog
- Create, edit, publish, and delete posts
- Markdown-based post authoring
- Tag filtering and post search
- RSS feeds for global and per-user content
- Comment creation, editing, and deletion
- Profile-linked author browsing

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
- Video uploads and management for superusers only
- Public video list page
- Protected media proxy routes so storage paths are not exposed in normal UI
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

### Caching and Background Work
- Redis-backed Django cache
- Media list caching for gallery, audio, and video pages
- Cache invalidation on media save/delete flows
- Celery worker and Celery Beat support
- Media sync helpers for cleaning broken references and orphan files

### Operations
- Docker Compose production stack
- PostgreSQL, Redis, Elasticsearch, Celery, Flower, Prometheus, Grafana, and Nginx support
- Health checks in the production stack
- Audit logging and backup support

## Main Routes

### Public
- `/blog/` - blog homepage
- `/blog/search/` - post search
- `/blog/audio/list/` - audio library
- `/blog/video/list/` - video library
- `/blog/gallery/` - gallery
- `/blog/album/` - albums
- `/users/login/` - login
- `/users/register/` - register

### Authenticated
- `/blog/create/` - create post
- `/blog/audio/upload/` - upload audio
- `/blog/gallery/upload/` - upload one image
- `/blog/album/upload/` - upload one album batch
- `/users/profile/` - profile page
- `/users/profile_edit/` - edit profile

### Superuser-only
- `/blog/video/upload/` - upload video
- `/blog/video/<id>/` - video detail
- `/blog/video/<id>/edit/` - video edit
- `/blog/video/<id>/delete/` - video delete

## Production Stack

Default services:
- `web`
- `db`
- `redis`
- `elasticsearch`
- `celery`
- `celery-beat`

Optional profile services:
- `flower`
- `prometheus`
- `grafana`
- `celery-exporter`
- `nginx`

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
cd /path/to/my_site_prod-master
```

2. Prepare the production environment file
Edit `.env.prod` and replace placeholder secrets before startup:
- `SECRET_KEY`
- `DB_PASSWORD`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `PROMETHEUS_EXTERNAL_URL`
- `GRAFANA_ROOT_URL`

3. Start the main production services
```bash
docker compose -f docker-compose.prod.yml up -d --build web db redis elasticsearch celery celery-beat
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
docker compose -f docker-compose.prod.yml --profile optional up -d --build flower prometheus grafana celery-exporter nginx
```

## Useful Commands

Rebuild application services:
```bash
docker compose -f docker-compose.prod.yml up -d --build web celery celery-beat
```

Rebuild local application services:
```bash
docker compose up -d --build web celery celery-beat
```

Run tests:
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py test
```

Run tests in the local stack:
```bash
docker compose exec web python manage.py test
```

Run the focused media/profile regression set:
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py test users.tests.test_users.test_profile images.tests.test_gallery_upload blog.tests.test_blog.test_audio blog.tests.test_blog.test_video --keepdb
```

## Project Structure

```text
my_site_prod-master/
|- blog/                    # Posts, comments, audio, video, feeds, API
|- users/                   # Authentication, profile, avatar, account settings
|- images/                  # Gallery and album features
|- my_site/                 # Settings, URLs, middleware, media helpers, runtime helpers
|- media/                   # Uploaded files
|- staticfiles/             # Collected static assets
|- logs/                    # Runtime logs
|- grafana/                 # Grafana provisioning
|- backups/                 # Backup files
|- .env.dev                 # Local environment template
|- .env.prod                # Production environment template
|- docker-compose.yml       # Local development stack
|- docker-compose.prod.yml
|- Dockerfile
|- nginx.conf
|- nginx.prod.conf
|- prometheus.yml
|- requirements.txt
|- README.md
`- my_site/templates/index.html
```

## Security Notes
- Protected media is served through proxy routes instead of exposing storage paths in normal UI
- Superuser-only video management routes redirect unauthorized users to blog home
- Denied protected routes return no-store / no-cache headers where configured
- Uploads are validated by file type and size
- Sensitive actions require authentication and ownership or superuser permission

## Current Notes
- Media list caching is active for gallery, audio, and video pages
- Deleted media is moved to `.trash`
- The project includes helper code for media cache invalidation and media file existence checks
