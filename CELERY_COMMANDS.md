# Celery Commands

## Goal

Use these commands to inspect, debug, and operate Celery worker, beat, and Flower services in this project.

## Worker Health

1. `docker compose exec celery celery -A my_site status`
2. `docker compose exec celery celery -A my_site inspect ping`
3. `docker compose exec celery celery -A my_site inspect active`
4. `docker compose exec celery celery -A my_site inspect reserved`
5. `docker compose exec celery celery -A my_site inspect scheduled`

Reason:

- These commands confirm the worker is alive and receiving tasks.
- They are the fastest checks when task execution looks stuck.

## Runtime Inspection

6. `docker compose exec celery celery -A my_site inspect stats`
7. `docker compose exec celery celery -A my_site inspect registered`
8. `docker compose exec celery celery -A my_site inspect revoked`
9. `docker compose exec celery celery -A my_site report`
10. `docker compose exec celery ps aux`
11. `docker compose exec celery-beat ps aux`

Reason:

- These commands help inspect worker registration, runtime state, and process layout.
- They are useful when a task exists in code but is not showing up at runtime.

## Events And Queue Control

12. `docker compose exec celery celery -A my_site control enable_events`
13. `docker compose exec celery celery -A my_site control disable_events`
14. `docker compose exec celery celery -A my_site purge`
15. `docker compose exec celery celery -A my_site call debug_task`
16. `docker compose exec celery celery -A my_site shell`

Reason:

- These commands are useful for event visibility, queue cleanup, and manual task testing.
- `purge` should be used carefully because it removes queued tasks.

## Logs

17. `docker compose logs -f celery`
18. `docker compose logs -f celery-beat`
19. `docker compose logs -f flower`

Reason:

- These commands are the first place to look for task failures and scheduler issues.
- They help distinguish worker, beat, and Flower problems.

## Service Control

20. `docker compose restart celery`
21. `docker compose restart celery-beat`
22. `docker compose restart flower`
23. `docker compose stop celery`
24. `docker compose stop celery-beat`
25. `docker compose start celery`
26. `docker compose start celery-beat`
27. `docker compose up -d celery`
28. `docker compose up -d celery-beat`
29. `docker compose up -d flower`

Reason:

- These commands control service lifecycle during deploys and debugging.
- They are the safest way to restart one Celery component without restarting the full stack.

## Django Side Checks

30. `docker compose exec celery python manage.py shell`
31. `docker compose exec web python manage.py shell`

Reason:

- These commands help verify Django settings, imports, and task registration from the app side.
- They are useful when Celery problems may actually come from Django configuration.
