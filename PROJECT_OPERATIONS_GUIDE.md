# Project Operations Guide

This document collects project-specific command examples for:

- 30 PostgreSQL `psql` operations
- 30 Django shell operations
- 20 Docker Compose operations

Split guides:

- `PSQL_GUIDE.md`
- `DJANGO_SHELL_GUIDE.md`
- `DOCKER_GUIDE.md`

Project root:

```powershell
cd G:\Projests\Python_Projects\my_site_prod-master
```

Default development services used below:

- database service: `db`
- Django service: `web`
- proxy service: `nginx`
- database name: `my_site_db`
- database user: `my_site_user`

Production commands are also shown where the compose file must be explicit.

## 30 PSQL Operations

All examples below are for this project database.

1. Open the project database shell:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db
```

2. Show all tables:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "\dt"
```

3. Describe the `blog_post` table:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "\d blog_post"
```

4. Describe the `blog_comment` table:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "\d blog_comment"
```

5. Describe the `blog_audiopost` table:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "\d blog_audiopost"
```

6. Describe the `users_profile` table:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "\d users_profile"
```

7. Count all blog posts:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "SELECT COUNT(*) FROM blog_post;"
```

8. Count only published blog posts:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "SELECT COUNT(*) FROM blog_post WHERE status = 'PB';"
```

9. Count draft blog posts:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "SELECT COUNT(*) FROM blog_post WHERE status = 'DF';"
```

10. Show latest 10 posts:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "SELECT id, title, slug, status, publish FROM blog_post ORDER BY publish DESC LIMIT 10;"
```

11. Show latest 10 comments:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "SELECT id, post_id, name, active, created FROM blog_comment ORDER BY created DESC LIMIT 10;"
```

12. Show latest 10 audio uploads:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "SELECT id, music_name, uploaded_by_id, active, created FROM blog_audiopost ORDER BY created DESC LIMIT 10;"
```

13. Count comments per post:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "SELECT post_id, COUNT(*) AS comment_count FROM blog_comment GROUP BY post_id ORDER BY comment_count DESC;"
```

14. Find posts with no comments:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "SELECT p.id, p.title FROM blog_post p LEFT JOIN blog_comment c ON c.post_id = p.id WHERE c.id IS NULL ORDER BY p.publish DESC;"
```

15. Find inactive comments:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "SELECT id, post_id, name, created FROM blog_comment WHERE active = false ORDER BY created DESC;"
```

16. Show posts by a specific author username:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "SELECT p.id, p.title, u.username FROM blog_post p JOIN auth_user u ON p.author_id = u.id WHERE u.username = 'admin' ORDER BY p.publish DESC;"
```

17. Show comments by a specific username:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "SELECT id, post_id, name, body, created FROM blog_comment WHERE name = 'admin' ORDER BY created DESC;"
```

18. Find duplicate post slugs on the same publish timestamp:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "SELECT slug, publish, COUNT(*) FROM blog_post GROUP BY slug, publish HAVING COUNT(*) > 1;"
```

19. Show latest registered users:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "SELECT id, username, email, date_joined FROM auth_user ORDER BY date_joined DESC LIMIT 10;"
```

20. Show user profiles with avatar info:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "SELECT user_id, location, birth_date, avatar, last_avatar_change FROM users_profile ORDER BY user_id;"
```

21. Show user activity logs:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "SELECT user_id, action, ip_address, timestamp FROM users_useractivity ORDER BY timestamp DESC LIMIT 20;"
```

22. Show user preferences:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "SELECT user_id, theme, email_notifications, push_notifications, comment_notifications FROM users_userpreference ORDER BY user_id;"
```

23. Show latest audit logs:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "SELECT id, user_id, method, path, status_code, response_time, timestamp FROM blog_auditlog ORDER BY timestamp DESC LIMIT 20;"
```

24. Find the biggest audio file names stored:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "SELECT id, music_name, audio_file, created FROM blog_audiopost ORDER BY created DESC LIMIT 20;"
```

25. Show tags and how many posts use each tag:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "SELECT t.name, COUNT(tp.object_id) AS usage_count FROM taggit_tag t JOIN taggit_taggeditem tp ON tp.tag_id = t.id GROUP BY t.name ORDER BY usage_count DESC;"
```

26. Show the last 7 days of posts:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "SELECT id, title, publish FROM blog_post WHERE publish >= NOW() - INTERVAL '7 days' ORDER BY publish DESC;"
```

27. Show comments with image attachments:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "SELECT id, post_id, name, image, created FROM blog_comment WHERE image IS NOT NULL AND image <> '';"
```

28. Check database size:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "SELECT pg_size_pretty(pg_database_size('my_site_db'));"
```

29. Show table sizes:

```powershell
docker compose exec db psql -U my_site_user -d my_site_db -c "SELECT relname AS table_name, pg_size_pretty(pg_total_relation_size(relid)) AS total_size FROM pg_catalog.pg_statio_user_tables ORDER BY pg_total_relation_size(relid) DESC;"
```

30. Run production database table listing:

```powershell
docker compose -f docker-compose.prod.yml exec db psql -U my_site_user -d my_site_db -c "\dt"
```

## 30 Django Shell Operations

All examples below run inside this project container.

1. Open Django shell:

```powershell
docker compose exec web python manage.py shell
```

2. Import the main project models:

```powershell
docker compose exec web python manage.py shell -c "from blog.models import Post, Comment, AudioPost, AuditLog; from users.models import Profile, UserActivity, UserPreference; from django.contrib.auth.models import User; print('imports ok')"
```

3. Count all posts:

```powershell
docker compose exec web python manage.py shell -c "from blog.models import Post; print(Post.objects.count())"
```

4. Count published posts:

```powershell
docker compose exec web python manage.py shell -c "from blog.models import Post; print(Post.published.count())"
```

5. Count draft posts:

```powershell
docker compose exec web python manage.py shell -c "from blog.models import Post; print(Post.objects.filter(status=Post.Status.DRAFT).count())"
```

6. Show the latest 5 posts:

```powershell
docker compose exec web python manage.py shell -c "from blog.models import Post; print(list(Post.objects.values_list('id', 'title', 'status')[:5]))"
```

7. Show the latest 5 published posts:

```powershell
docker compose exec web python manage.py shell -c "from blog.models import Post; print(list(Post.published.values_list('title', flat=True)[:5]))"
```

8. Show a post absolute URL:

```powershell
docker compose exec web python manage.py shell -c "from blog.models import Post; p = Post.published.first(); print(p.get_absolute_url() if p else 'no post')"
```

9. List posts by a specific author:

```powershell
docker compose exec web python manage.py shell -c "from blog.models import Post; print(list(Post.objects.filter(author__username='admin').values_list('title', flat=True)[:10]))"
```

10. List comments for the newest post:

```powershell
docker compose exec web python manage.py shell -c "from blog.models import Post; p = Post.published.first(); print(list(p.comments.values_list('name', 'body')[:10]) if p else [])"
```

11. Count comments per published post:

```powershell
docker compose exec web python manage.py shell -c "from blog.models import Post; from django.db.models import Count; print(list(Post.published.annotate(comment_count=Count('comments')).values_list('title', 'comment_count')[:10]))"
```

12. Show inactive comments:

```powershell
docker compose exec web python manage.py shell -c "from blog.models import Comment; print(list(Comment.objects.filter(active=False).values_list('id', 'name', 'created')[:10]))"
```

13. Show latest audio posts:

```powershell
docker compose exec web python manage.py shell -c "from blog.models import AudioPost; print(list(AudioPost.objects.values_list('music_name', 'audio_file')[:10]))"
```

14. Show audio posts uploaded by a user:

```powershell
docker compose exec web python manage.py shell -c "from blog.models import AudioPost; print(list(AudioPost.objects.filter(uploaded_by__username='admin').values_list('music_name', flat=True)[:10]))"
```

15. Count users:

```powershell
docker compose exec web python manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.count())"
```

16. Show latest users:

```powershell
docker compose exec web python manage.py shell -c "from django.contrib.auth.models import User; print(list(User.objects.values_list('username', 'email')[:10]))"
```

17. Show all profiles:

```powershell
docker compose exec web python manage.py shell -c "from users.models import Profile; print(list(Profile.objects.values_list('user__username', 'location')[:10]))"
```

18. Show users who can change avatar now:

```powershell
docker compose exec web python manage.py shell -c "from users.models import Profile; print([p.user.username for p in Profile.objects.select_related('user') if p.can_change_avatar()][:10])"
```

19. Show user activities:

```powershell
docker compose exec web python manage.py shell -c "from users.models import UserActivity; print(list(UserActivity.objects.values_list('user__username', 'action', 'timestamp')[:10]))"
```

20. Show user preferences:

```powershell
docker compose exec web python manage.py shell -c "from users.models import UserPreference; print(list(UserPreference.objects.values_list('user__username', 'theme')[:10]))"
```

21. Show latest audit logs:

```powershell
docker compose exec web python manage.py shell -c "from blog.models import AuditLog; print(list(AuditLog.objects.values_list('method', 'path', 'status_code')[:20]))"
```

22. Find posts missing tags:

```powershell
docker compose exec web python manage.py shell -c "from blog.models import Post; print([p.title for p in Post.objects.all() if p.tags.count() == 0][:20])"
```

23. Find posts with duplicate titles:

```powershell
docker compose exec web python manage.py shell -c "from blog.models import Post; from django.db.models import Count; print(list(Post.objects.values('title').annotate(c=Count('id')).filter(c__gt=1)[:20]))"
```

24. Create a draft post from shell:

```powershell
docker compose exec web python manage.py shell -c "from blog.models import Post; from django.contrib.auth.models import User; from django.utils import timezone; u = User.objects.first(); p = Post.objects.create(title='Shell Draft Example', body='Created from shell', author=u, status=Post.Status.DRAFT, publish=timezone.now()); print(p.id if u else 'no user')"
```

25. Publish an existing draft post:

```powershell
docker compose exec web python manage.py shell -c "from blog.models import Post; p = Post.objects.filter(status=Post.Status.DRAFT).first(); print('no draft' if not p else setattr(p, 'status', Post.Status.PUBLISHED) or p.save() or p.id)"
```

26. Add tags to the latest draft post:

```powershell
docker compose exec web python manage.py shell -c "from blog.models import Post; p = Post.objects.filter(status=Post.Status.DRAFT).first(); print('no draft' if not p else p.tags.add('shell', 'manual') or list(p.tags.names()))"
```

27. Create a comment on the latest published post:

```powershell
docker compose exec web python manage.py shell -c "from blog.models import Post, Comment; p = Post.published.first(); c = Comment.objects.create(post=p, name='shell-user', email='shell@example.com', body='Created from shell') if p else None; print(c.id if c else 'no post')"
```

28. Deactivate the newest comment:

```powershell
docker compose exec web python manage.py shell -c "from blog.models import Comment; c = Comment.objects.order_by('-created').first(); print('no comment' if not c else setattr(c, 'active', False) or c.save() or c.id)"
```

29. Render markdown for the newest published post:

```powershell
docker compose exec web python manage.py shell -c "from blog.models import Post; p = Post.published.first(); print(p.get_markdown_body()[:500] if p else 'no post')"
```

30. Run Django shell in production settings:

```powershell
docker compose -f docker-compose.prod.yml exec web python manage.py shell
```

## 20 Docker Compose Operations

These are common commands specifically for this project.

1. Start the development stack:

```powershell
docker compose up --build -d
```

2. Show current development containers:

```powershell
docker compose ps
```

3. Show development web logs:

```powershell
docker compose logs --tail=100 web
```

4. Show development nginx logs:

```powershell
docker compose logs --tail=100 nginx
```

5. Show development db logs:

```powershell
docker compose logs --tail=100 db
```

6. Restart only the web service:

```powershell
docker compose restart web
```

7. Rebuild only the web image:

```powershell
docker compose build web
```

8. Open a shell in the web container:

```powershell
docker compose exec web sh
```

9. Open a shell in the db container:

```powershell
docker compose exec db sh
```

10. Run migrations:

```powershell
docker compose exec web python manage.py migrate
```

11. Collect static files:

```powershell
docker compose exec web python manage.py collectstatic --noinput
```

12. Run all tests:

```powershell
docker compose exec web python manage.py test
```

13. Run infrastructure tests:

```powershell
docker compose exec web python manage.py test my_site.tests_infrastructure
```

14. Check database readiness:

```powershell
docker compose exec db pg_isready -U my_site_user -d my_site_db
```

15. Stop the current stack:

```powershell
docker compose stop
```

16. Start the production stack:

```powershell
docker compose -f docker-compose.prod.yml up --build -d
```

17. Show production containers:

```powershell
docker compose -f docker-compose.prod.yml ps
```

18. Show production web logs:

```powershell
docker compose -f docker-compose.prod.yml logs --tail=100 web
```

19. Run production migrations:

```powershell
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

20. Open production database shell:

```powershell
docker compose -f docker-compose.prod.yml exec db psql -U my_site_user -d my_site_db
```

## Observability Operations

These commands cover the project's Celery, Flower, Prometheus, Grafana, and Sentry-related checks.

1. Show observability service status:

```powershell
docker compose ps celery celery-beat flower prometheus grafana celery-exporter
```

2. Check Celery worker control path:

```powershell
docker compose exec celery celery -A my_site inspect ping
```

3. Check Celery worker status:

```powershell
docker compose exec celery celery -A my_site status
```

4. Tail Celery logs:

```powershell
docker compose logs --tail=100 celery
```

5. Tail Flower logs:

```powershell
docker compose logs --tail=100 flower
```

6. Open Flower:

```text
http://localhost:5555/
```

7. Check Django Prometheus metrics through Nginx:

```powershell
curl http://localhost/metrics
```

8. Check celery-exporter metrics:

```powershell
curl http://localhost:9540/metrics
```

9. Check Prometheus active targets:

```powershell
curl http://localhost:9090/api/v1/targets
```

10. Check Grafana health:

```powershell
curl http://localhost:3000/api/health
```

11. Tail Prometheus logs:

```powershell
docker compose logs --tail=100 prometheus
```

12. Tail Grafana logs:

```powershell
docker compose logs --tail=100 grafana
```

13. Confirm Grafana dashboard provisioning files inside the container:

```powershell
docker compose exec grafana sh -c "ls -R /etc/grafana/provisioning/dashboards"
```

14. Run observability integration tests:

```powershell
docker compose exec web python manage.py test my_site.tests_celery_integration my_site.tests_sentry_integration my_site.tests_prometheus_integration my_site.tests_grafana_integration
```

15. Check whether Sentry is enabled in the web container:

```powershell
docker compose exec web python manage.py shell -c "from django.conf import settings; print(bool(settings.SENTRY_DSN))"
```

16. Check whether Sentry is enabled in the Celery container:

```powershell
docker compose exec celery python -c "from django.conf import settings; print(bool(settings.SENTRY_DSN))"
```

17. Recover from `/blog/` returning `502` after `web` recreation:

```powershell
docker compose restart nginx
curl http://localhost/blog/
```

18. Recover from Prometheus `django` target showing `down`:

```powershell
docker compose restart prometheus
curl http://localhost:9090/api/v1/targets
```

19. Restart Grafana after provisioning changes:

```powershell
docker compose restart grafana
```

20. Restart Flower after Celery worker event changes:

```powershell
docker compose restart flower
```

## Safety Notes

- Do not use plain `docker compose up` on the server. Use `docker-compose.prod.yml`.
- Do not run destructive commands against the wrong database.
- Review shell write commands before running them on production.
- The examples above include both read-only inspection commands and write commands. Please check the intent before execution.
