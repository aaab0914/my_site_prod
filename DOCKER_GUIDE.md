# Docker Guide

This file contains 20 common Docker Compose operations for `my_site_prod-master`.

Project root:

```powershell
cd G:\Projests\Python_Projects\my_site_prod-master
```

Default services:

- Django: `web`
- PostgreSQL: `db`
- Nginx: `nginx`

Production file:

```text
docker-compose.prod.yml
```

## 20 Docker Compose Operations

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

## Notes

- Use `docker-compose.prod.yml` on the server.
- Do not use plain `docker compose up` for production.
- Do not run `docker-compose down -v`.
