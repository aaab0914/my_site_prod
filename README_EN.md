# My Site - Django Blog Platform

A modern, production-ready blog platform built with Django, featuring a comprehensive content management system, REST API, and Docker deployment.

## ✨ Features

### Blog Management
- **Post Publishing**: Create, edit, delete blog posts with draft/published status
- **Rich Text Editor**: Markdown support with live preview via django-markdownx
- **Tagging System**: Tag-based post filtering and categorization
- **Search Functionality**: Full-text search across posts and comments
- **RSS Feed**: Automatic feed generation for content syndication
- **Audio Upload**: Host audio files directly on the platform
- **Comments**: User comment system with moderation

### User Management
- **User Authentication**: Secure registration, login, and profile management
- **Profile Customization**: Bio, location, birth date, and avatar upload
- **Avatar Rate Limiting**: Prevent frequent avatar changes (3-day cooldown)
- **Activity Logging**: Track user actions and login history
- **User Preferences**: Theme selection and notification settings
- **Account Management**: User deletion and username changes

### Media Management
- **Image Hosting**: Upload and manage images
- **Audio Streaming**: Host and serve audio files
- **Automatic Organization**: Date-based folder structure (YYYY/MM/DD/)

### API & Integration
- **REST API**: Full REST API for posts, comments, and tags
- **Token Authentication**: Secure API access with token-based auth
- **API Documentation**: Comprehensive endpoint documentation
- **Django Admin**: Complete backend management interface

### DevOps & Monitoring
- **Docker Deployment**: Complete Docker Compose setup with PostgreSQL and Nginx
- **Automatic Backup**: Database backups every 3 days with 7-day retention
- **Request Logging**: Audit trail of all HTTP requests with IP tracking
- **CI/CD Pipeline**: GitHub Actions for automated testing
- **Unit Tests**: 29+ test cases covering models, views, and forms

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose plugin
- Python 3.12+
- PostgreSQL 16

### Installation

1. **Clone and setup**:
```bash
cd my_site_prod-master
```

2. **Configure environment**:
```bash
# Create .env from the tracked template
cp .env.example .env
```

3. **Start containers**:
```bash
docker compose up -d
```

4. **Run migrations**:
```bash
docker compose exec web python manage.py migrate
```

5. **Create superuser**:
```bash
docker compose exec web python manage.py createsuperuser
```

6. **Collect static files**:
```bash
docker compose exec web python manage.py collectstatic --noinput
```

7. **Access the application**:
- Blog: http://localhost/blog/
- Admin: http://localhost/admin/
- API: http://localhost/blog/api/

## 📁 Project Structure

```
my_site_prod-master/
├── blog/                    # Blog app (posts, comments, audio)
├── users/                   # User management app
├── images/                  # Image hosting app
├── my_site/                # Project settings and config
├── media/                   # User uploads (images, audio)
├── staticfiles/             # Collected static files
├── logs/                    # Application logs
├── backups/                 # Database backups
├── docker-compose.yml       # Docker configuration
├── Dockerfile               # Container build config
├── nginx.conf              # Reverse proxy config
├── requirements.txt        # Python dependencies
└── manage.py               # Django CLI
```

## 🔧 Technology Stack

**Backend:**
- Django 6.0.2 (Latest LTS)
- Django REST Framework 3.15
- PostgreSQL 16
- Gunicorn 25.3

**Frontend:**
- Nginx 1.25 (Reverse Proxy)
- HTML/CSS/JavaScript
- Django Templates

**Tools & Libraries:**
- django-taggit: Tag management
- django-markdownx: Markdown editor
- Pillow: Image processing
- python-decouple: Environment variables

**DevOps:**
- Docker & Docker Compose
- GitHub Actions CI/CD
- Shell scripts for backups

## 📊 API Documentation

See `API_DOCUMENTATION.md` for complete API reference.

### Common Endpoints:
```
GET    /blog/api/posts/           # List all posts
POST   /blog/api/posts/           # Create new post
GET    /blog/api/posts/{id}/      # Get post detail
PUT    /blog/api/posts/{id}/      # Update post
DELETE /blog/api/posts/{id}/      # Delete post

GET    /blog/api/comments/        # List comments
POST   /blog/api/comments/        # Create comment
GET    /blog/api/tags/            # List tags
```

## 🧪 Testing

Run the test suite:
```bash
# All tests
docker compose exec web python manage.py test

# Specific app
docker compose exec web python manage.py test blog
docker compose exec web python manage.py test users
docker compose exec web python manage.py test images

# With verbosity
docker compose exec web python manage.py test --verbosity=2
```

**Current Coverage**: 29 test cases
- Blog models and views
- User authentication and profiles
- API endpoints
- Image uploads

## 🔐 Security Features

- CSRF protection enabled
- SQL injection prevention (ORM)
- XSS protection via template escaping
- Secure password hashing
- HTTPS-ready configuration
- User authentication required for sensitive operations
- Input validation on all forms
- Login rate limiting after repeated failures
- Upload file type and size restrictions for avatars, cover images, and audio files

## 📈 Monitoring & Logs

**Log Files:**
- `logs/YYYY-MM/django-YYYY-MM-DD.log` - Application logs
- `logs/YYYY-MM/error-YYYY-MM-DD.log` - Warning and error logs
- `logs/YYYY-MM/gunicorn-access-YYYY-MM-DD.log` - Gunicorn access logs
- `logs/YYYY-MM/gunicorn-error-YYYY-MM-DD.log` - Gunicorn error logs
- `logs/backup.log` - Backup operation logs

Legacy flat files such as `logs/django.log`, `logs/error.log`, and `logs/access.log`
may still exist from older runs, but active application logging now targets the
dated files under `logs/YYYY-MM/`.

**Audit Log:**
- Request tracking in Django Admin
- User action history
- IP address logging

**Database Backups:**
- Located in `backups/db/`
- Automatic backups every 3 days
- 7-day retention policy
- Manual backup: `./backup_db.sh`
- Manual backup on Windows PowerShell: `.\backup_db.ps1`
- Restore drill on Windows PowerShell: `.\restore_test.ps1`

## 🚀 Deployment

### Development
```bash
docker compose up
```

### Production
1. Set environment variables in `.env`
2. Enable HTTPS in nginx.conf
3. Set DEBUG=False
4. Configure ALLOWED_HOSTS
5. Configure `CSRF_TRUSTED_ORIGINS`
6. Set up SSL certificates
7. Start services with `docker compose -f docker-compose.prod.yml up --build -d`
8. Run `bash ./deploy-prod.sh` for deploy-time checks, migrations, static collection, and smoke tests

## 📝 Configuration

### Environment Variables (.env)
Use `.env.example` as the committed production-safe template.

```
SECRET_KEY=your-django-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com

# Database
DB_NAME=my_site_db
DB_USER=my_site_user
DB_PASSWORD=your-strong-password
DB_HOST=db
DB_PORT=5432

# HTTPS
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

## 🐛 Troubleshooting

**Port already in use:**
```bash
docker compose down
docker compose up -d
```

**Database migration issues:**
```bash
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
```

**Media files not visible:**
```bash
docker compose exec web python manage.py collectstatic --noinput
```

**Permission denied on scripts:**
```bash
chmod +x backup_db.sh
chmod +x backup_loop.sh
```

## 📞 Support & Documentation

- Django Documentation: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- API Documentation: See `API_DOCUMENTATION.md`
- Admin Panel: http://localhost/admin/

## 📜 License

This project is open source and available under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:
1. Create a feature branch
2. Make your changes
3. Write/update tests
4. Submit a pull request

## ✅ Quality Metrics

- **Code Coverage**: 29 test cases
- **Python Version**: 3.12
- **Django Version**: 6.0.2
- **API Status**: Fully operational
- **Deployment**: Docker-ready

---

**Last Updated**: June 2026  
**Version**: 1.0.0  
**Status**: Production Ready ✅
