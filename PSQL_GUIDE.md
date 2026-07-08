# PSQL Guide

This file contains 30 project-specific PostgreSQL `psql` operations for `my_site_prod-master`.

Project root:

```powershell
cd G:\Projests\Python_Projects\my_site_prod-master
```

Default database target:

- service: `db`
- database: `my_site_db`
- user: `my_site_user`

## 30 PSQL Operations

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
