# Django Shell Guide

This file contains 30 project-specific Django shell operations for `my_site_prod-master`.

Project root:

```powershell
cd C:\Users\K1457\Downloads\Compressed\my_site_prod-master
```

Default Django target:

- service: `web`
- development settings: `my_site.settings.dev`

## 30 Django Shell Operations

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
