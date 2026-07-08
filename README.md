# My Site - Django Blog Platform

> A modern, production-ready Django platform for blogging, media publishing, account management, and Docker-based deployment.

## ✨ Features

### Blog Management
- **Post Publishing**: Create, edit, delete, and manage draft or published posts
- **Rich Text Editor**: Markdown authoring with live preview via `django-markdownx`
- **Tagging System**: Tag-based filtering and categorization
- **Search Functionality**: Full-text style search across posts and comments
- **RSS Feed**: Built-in content syndication
- **Audio Upload**: Upload and host audio directly on the platform
- **Comments**: User comment flow with moderation support

### User Management
- **User Authentication**: Registration, login, logout, and profile management
- **Profile Customization**: Bio, location, birth date, and avatar upload
- **Avatar Rate Limiting**: 3-day cooldown to reduce abuse
- **Activity Logging**: Track user actions and login history
- **User Preferences**: Theme and notification settings
- **Account Management**: Username changes and account deletion

### Media Management
- **Image Hosting**: Upload and manage gallery images
- **Audio Streaming**: Serve audio files from the platform
- **Automatic Organization**: Date-based media storage layout

### API & Integration
- **REST API**: API endpoints for posts, comments, and tags
- **Token Authentication**: Secure token-based access
- **API Documentation**: Reference available in `API_DOCUMENTATION.md`
- **Django Admin**: Full backend management interface

### DevOps & Monitoring
- **Docker Deployment**: Compose-based stack with PostgreSQL and Nginx
- **Automatic Backup**: Scheduled backups with retention
- **Request Logging**: Audit trail with IP tracking
- **CI/CD Pipeline**: GitHub Actions workflow support
- **Unit Tests**: Coverage across models, views, forms, and uploads

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose plugin
- Python 3.12+
- PostgreSQL 16

### Installation

1. **Enter the project directory**
```bash
cd my_site_prod-master
```

2. **Create your environment file**
```bash
cp .env.example .env
```

3. **Start the stack**
```bash
docker compose up -d
```

4. **Run migrations**
```bash
docker compose exec web python manage.py migrate
```

5. **Create a superuser**
```bash
docker compose exec web python manage.py createsuperuser
```

6. **Collect static files**
```bash
docker compose exec web python manage.py collectstatic --noinput
```

7. **Open the application**

| Area | URL |
| --- | --- |
| Blog | `http://localhost/blog/` |
| Admin | `http://localhost/admin/` |
| API | `http://localhost/blog/api/` |

## 📁 Project Structure

```text
my_site_prod-master/
|- blog/              # Blog app: posts, comments, audio
|- users/             # Authentication and profile management
|- images/            # Gallery and image hosting
|- my_site/           # Settings, root URLs, metrics, middleware
|- media/             # User-uploaded files
|- staticfiles/       # Collected static assets
|- logs/              # Application and runtime logs
|- backups/           # Database backups
|- docker-compose.yml
|- docker-compose.prod.yml
|- Dockerfile
|- nginx.conf
|- requirements.txt
`- manage.py
```

## 🔧 Technology Stack

| Layer | Tools |
| --- | --- |
| Backend | Django 6.0.2, Django REST Framework, Gunicorn |
| Data | PostgreSQL 16 |
| Frontend | Django Templates, HTML, CSS, JavaScript |
| Media | Pillow, django-markdownx |
| DevOps | Docker, Docker Compose, GitHub Actions |

### Supporting Libraries

- `django-taggit`
- `django-markdownx`
- `Pillow`
- `python-decouple`

## 📊 API Documentation

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for the full API reference.

### Common Endpoints

```text
GET    /blog/api/posts/           List all posts
POST   /blog/api/posts/           Create a post
GET    /blog/api/posts/{id}/      Retrieve one post
PUT    /blog/api/posts/{id}/      Update one post
DELETE /blog/api/posts/{id}/      Delete one post

GET    /blog/api/comments/        List comments
POST   /blog/api/comments/        Create a comment
GET    /blog/api/tags/            List tags
```

## 🧪 Testing

Run the full test suite:

```bash
docker compose exec web python manage.py test
```

Run tests by app:

```bash
docker compose exec web python manage.py test blog
docker compose exec web python manage.py test users
docker compose exec web python manage.py test images
```

Verbose output:

```bash
docker compose exec web python manage.py test --verbosity=2
```

<details>
<summary>Coverage Areas</summary>

- Blog models and views
- User authentication and profile flows
- API endpoints
- Image and audio uploads

</details>

## 🔐 Security Features

- CSRF protection enabled
- ORM-based SQL injection protection
- Template escaping for XSS mitigation
- Secure password hashing
- HTTPS-ready deployment settings
- Authentication required for sensitive actions
- Validation on forms and uploads
- Login rate limiting after repeated failures
- Upload size and file-type restrictions for avatars, cover images, and audio

## 📈 Monitoring & Logs

### Log Files

- `logs/YYYY-MM/django-YYYY-MM-DD.log`
- `logs/YYYY-MM/error-YYYY-MM-DD.log`
- `logs/YYYY-MM/gunicorn-access-YYYY-MM-DD.log`
- `logs/YYYY-MM/gunicorn-error-YYYY-MM-DD.log`
- `logs/backup.log`

Legacy flat files may still exist, but active logging targets the dated files under `logs/YYYY-MM/`.

### Audit Log

- Request tracking in Django Admin
- User action history
- IP address logging

### Database Backups

- Stored in `backups/db/`
- Automatic backup schedule with retention
- Manual Linux backup: `./backup_db.sh`
- Manual PowerShell backup: `.\backup_db.ps1`
- Restore drill: `.\restore_test.ps1`

## 🚀 Deployment

### Development

```bash
docker compose up
```

### Production

1. Set values in `.env`
2. Enable HTTPS in `nginx.conf`
3. Set `DEBUG=False`
4. Configure `ALLOWED_HOSTS`
5. Configure `CSRF_TRUSTED_ORIGINS`
6. Install SSL certificates
7. Start services with:
```bash
docker compose -f docker-compose.prod.yml up --build -d
```
8. Run deploy checks:
```bash
bash ./deploy-prod.sh
```

## 📝 Configuration

### Environment Variables

Use `.env.example` as the committed template.

```env
SECRET_KEY=your-django-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com

DB_NAME=my_site_db
DB_USER=my_site_user
DB_PASSWORD=your-strong-password
DB_HOST=db
DB_PORT=5432

SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
CSRF_COOKIE_HTTPONLY=True
SESSION_COOKIE_HTTPONLY=True
SECURE_HSTS_SECONDS=31536000
```

Do not commit the real `.env`. Commit `.env.example` only.

Validate production values before deployment:

```bash
python validate_prod_env.py
```

## 📚 Related Docs

- [DOCKER_GUIDE.md](./DOCKER_GUIDE.md)
- [PROJECT_OPERATIONS_GUIDE.md](./PROJECT_OPERATIONS_GUIDE.md)
- [PRODUCTION_VERIFICATION.md](./PRODUCTION_VERIFICATION.md)
- [OBSERVABILITY_RUNBOOK.md](./OBSERVABILITY_RUNBOOK.md)
- [TEST_INDEX.md](./TEST_INDEX.md)

## Current Notes

- The production stack in this repository includes more than a minimal blog because it also carries observability and operational tooling.
- Some security warnings may still appear if local `.env` values are intentionally development-oriented.
