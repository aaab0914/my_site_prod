# PSQL Commands

## Goal

Use these commands after you have already entered the `psql` prompt.

## Connect First

Use a command like this before the commands below:

`docker compose exec db psql -U my_site_user -d my_site_db`

## Database Info

1. `\l`
2. `\c my_site_db`
3. `\conninfo`
4. `\dt`
5. `\dt blog_*`
6. `\dt users_*`

Reason:

- These commands help you confirm which database you are using.
- They give a quick view of tables and schema layout.

## Schema Inspection

7. `\d blog_post`
8. `\d blog_comment`
9. `\d blog_auditlog`
10. `\d users_profile`
11. `\d auth_user`
12. `\dn`

Reason:

- These commands show table structure, columns, indexes, and constraints.
- They are useful before writing queries or checking migrations.

## Basic Counts

13. `SELECT COUNT(*) FROM blog_post;`
14. `SELECT COUNT(*) FROM blog_comment;`
15. `SELECT COUNT(*) FROM blog_auditlog;`
16. `SELECT COUNT(*) FROM auth_user;`
17. `SELECT COUNT(*) FROM users_profile;`
18. `SELECT COUNT(*) FROM django_migrations;`

Reason:

- These commands are simple health checks for imported or migrated data.
- They are useful after restores and deployments.

## Content Queries

19. `SELECT id, title, status, publish FROM blog_post ORDER BY publish DESC LIMIT 10;`
20. `SELECT id, username, email, is_superuser FROM auth_user ORDER BY id;`
21. `SELECT id, path, method, status_code, timestamp FROM blog_auditlog ORDER BY timestamp DESC LIMIT 10;`
22. `SELECT id, post_id, email, active, created FROM blog_comment ORDER BY created DESC LIMIT 10;`
23. `SELECT user_id, location, birth_date FROM users_profile ORDER BY user_id;`
24. `SELECT app, name, applied FROM django_migrations ORDER BY applied DESC LIMIT 20;`

Reason:

- These commands help inspect real records without leaving `psql`.
- They are useful for debugging content, users, audit logs, and migrations.

## Aggregates

25. `SELECT status, COUNT(*) FROM blog_post GROUP BY status;`
26. `SELECT author_id, COUNT(*) AS post_count FROM blog_post GROUP BY author_id ORDER BY post_count DESC;`
27. `SELECT active, COUNT(*) FROM blog_comment GROUP BY active;`
28. `SELECT method, COUNT(*) FROM blog_auditlog GROUP BY method ORDER BY count DESC;`
29. `SELECT status_code, COUNT(*) FROM blog_auditlog GROUP BY status_code ORDER BY status_code;`
30. `SELECT DATE(timestamp), COUNT(*) FROM blog_auditlog GROUP BY DATE(timestamp) ORDER BY DATE(timestamp) DESC;`

Reason:

- These commands summarize application behavior and content state.
- They are useful for quick reporting and troubleshooting.
