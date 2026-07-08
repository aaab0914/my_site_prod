# Nginx Commands

## Goal

Use these commands to validate, inspect, and operate the Nginx reverse proxy in this project.

## Validate Config

1. `docker compose exec nginx nginx -t`
2. `docker compose exec nginx nginx -T`
3. `docker compose exec nginx cat /etc/nginx/conf.d/default.conf`
4. `docker compose exec nginx grep -n "server" /etc/nginx/conf.d/default.conf`
5. `docker compose exec nginx grep -n "location" /etc/nginx/conf.d/default.conf`

Reason:

- These commands verify that the config is valid and readable.
- They are the first step when routes, static files, or proxying break.

## Reload And Process Control

6. `docker compose exec nginx nginx -s reload`
7. `docker compose exec nginx nginx -s reopen`
8. `docker compose exec nginx nginx -s quit`
9. `docker compose restart nginx`
10. `docker compose stop nginx`
11. `docker compose start nginx`
12. `docker compose up -d nginx`

Reason:

- These commands control the Nginx process without changing application code.
- `reload` is the normal choice after config updates.

## Check Files And Mounts

13. `docker compose exec nginx ls -la /etc/nginx/conf.d`
14. `docker compose exec nginx ls -la /static`
15. `docker compose exec nginx ls -la /media`
16. `docker compose exec nginx stat /etc/nginx/conf.d/default.conf`
17. `docker compose exec nginx find /etc/nginx -maxdepth 2 -type f`

Reason:

- These commands verify that bind mounts and config files exist in the container.
- They are useful when static or media serving is broken.

## Test Requests

18. `docker compose exec nginx curl -I http://127.0.0.1`
19. `docker compose exec nginx curl -I http://127.0.0.1/users/login/`
20. `curl -I http://localhost`
21. `curl -I http://localhost/users/login/`
22. `docker compose exec nginx wget -S -O - http://web:8000/users/login/`

Reason:

- These commands check both external and internal request paths.
- They help isolate whether the problem is in Nginx or in Django.

## Logs And Environment

23. `docker compose logs -f nginx`
24. `docker compose logs --tail=100 nginx`
25. `docker compose exec nginx ps aux`
26. `docker compose exec nginx nginx -V`
27. `docker compose exec nginx env`
28. `docker compose exec nginx sh`
29. `docker compose exec nginx netstat -tulpn`
30. `docker compose exec nginx ss -tulpn`

Reason:

- These commands are useful for runtime inspection and troubleshooting.
- They show logs, worker processes, binary build info, and open ports.
