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

## Run with Docker Compose

```bash
docker compose up --build -d
```

Open the site:

- `http://localhost/blog/`
- `http://localhost/users/login/`
- `http://localhost/users/register/`

## Run Migrations

```bash
docker compose exec web python manage.py migrate
```

## Collect Static Files

```bash
docker compose exec web python manage.py collectstatic --noinput
```

## Production Notes

- Current configuration is suitable for HTTP deployment behind Nginx.
- HTTPS-related Django security switches should only be enabled after Nginx is configured with TLS.
- Nginx serves `/static/` and `/media/` directly.
- PostgreSQL runs in the `db` service defined in `docker-compose.yml`.

## Development Notes

- Source CSS is in `static/`.
- Externally served static assets may come from `staticfiles/` after collection or manual sync, depending on the deployment flow.
- Audio upload requires login.
