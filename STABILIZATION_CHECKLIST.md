# Project Stabilization Checklist

This checklist is for the current Docker-based Django project in `my_site_prod-master`.

The goal is to stop adding new features and move the project into a stable, maintainable state.

## Must Fix Now

### 1. Remove hard-coded secrets from `docker-compose.yml`

Current risk:

- `POSTGRES_PASSWORD: Coffee.1`
- `DB_PASSWORD: Coffee.1`

Why this matters:

- Secrets are currently stored in source-controlled infrastructure config.
- This is unsafe for server deployment and easy to leak.

Action:

- Move database credentials to `.env`
- Change `docker-compose.yml` to use environment substitution
- Rotate the current database password after updating the server

### 2. Separate development and production behavior

Current risk:

- The same Compose file is trying to serve both local development and server deployment.
- `- .:/code` is convenient for development but fragile in production.

Why this matters:

- Bind mounts can override container files and permissions.
- Production should not depend on mutable source mounts unless there is a clear operational reason.

Action:

- Keep current `docker-compose.yml` for development if needed
- Add a production-specific Compose file without `- .:/code`
- Only mount persistent directories such as `media`, `staticfiles`, and backups in production

### 3. Lock down entrypoint and startup behavior

Current risk:

- This already caused a real `permission denied` issue on the server.

Status:

- Partially mitigated by moving the entrypoint to `/usr/local/bin/entrypoint.sh`

Action:

- Rebuild the `web` image on the server
- Verify startup after rebuild
- Keep a test that prevents regression to `/code/entrypoint.sh`

### 4. Review login gating rules

Current risk:

- `LoginRequiredMiddleware` globally redirects unauthenticated users except for a short allowlist.
- This can easily break public pages, detail pages, feeds, APIs, and future routes.

Why this matters:

- It is easy to accidentally hide content or create SEO and API regressions.
- Global path allowlists do not scale well.

Action:

- Decide which routes are public and which are private
- Replace path-based global restrictions with per-view protection where practical
- Explicitly test public routes after any access-control change

### 5. Verify backup and restore on real data

Current risk:

- Backup scripts exist, but restore confidence is not the same as restore proof.

Why this matters:

- A backup is only useful if restore is tested.

Action:

- Take a fresh backup
- Restore it into a safe test database or test environment
- Verify `/blog/`, login, admin, and media behavior after restore

## Should Fix This Week

### 6. Replace text-based config assertions with stronger environment validation where useful

Current status:

- Infrastructure tests now protect `nginx.conf`, `docker-compose.yml`, and startup assumptions.

Next step:

- Keep these tests
- Add a small number of host-side checks for server workflows

Examples:

- `docker compose config`
- `docker compose ps`
- `docker compose exec db pg_isready`

### 7. Add more route-level integration tests

Current status:

- Key tests were added for:
  - `/blog/`
  - `/blog/<detail>/`
  - `/blog/create/`
  - `/blog/audio/list/`

Next step:

- Add tests for:
  - `/users/register/`
  - `/users/login/`
  - `/users/profile/`
  - `/blog/search/`
  - one successful `POST` to `/blog/create/`

### 8. Audit model constraints and duplicate-content risks

Why this matters:

- Earlier failures showed that route behavior can break when data uniqueness assumptions are violated.

Action:

- Review `Post` uniqueness logic and detail lookup assumptions
- Check for duplicate slugs, null-like edge cases, and invalid publish values
- Add management commands or admin checks for bad content rows

### 9. Review upload limits and file-handling behavior

Why this matters:

- Upload-related failures have already appeared in logs.

Action:

- Re-check:
  - `DATA_UPLOAD_MAX_MEMORY_SIZE`
  - `FILE_UPLOAD_MAX_MEMORY_SIZE`
  - Nginx `client_max_body_size`
- Test realistic image and audio uploads
- Confirm media permissions on the server after deployment

### 10. Clean up Dockerfile duplication and tighten image quality

Current issue:

- The old Dockerfile had duplicated entrypoint copy logic.

Action:

- Keep the new single entrypoint path
- Consider using the `app` user explicitly for runtime once permissions are verified
- Keep the image predictable and minimal

## Can Improve Later

### 11. Split settings by environment

Suggested target:

- `settings/base.py`
- `settings/dev.py`
- `settings/prod.py`

Why:

- Cleaner security defaults
- Fewer accidental production mistakes

### 12. Improve logging strategy

Current state:

- Logs are written to files and container logs also exist.

Later improvement:

- Decide which source is primary during operations
- Keep structured logs if the project grows further

### 13. Add health endpoints and readiness checks

Examples:

- `/healthz`
- database connectivity check
- application readiness check

Why:

- Helps reverse proxy and deployment checks
- Makes incident diagnosis faster

### 14. Formalize deployment and rollback steps

Add a short operational playbook for:

- deploy
- rebuild
- migrate
- verify
- rollback

### 15. Review static and media strategy for long-term production use

If the project grows:

- consider dedicated object storage or CDN-backed media delivery
- keep local media only if server operations remain simple and low traffic

## Working Rule For Now

Until the checklist above is mostly complete:

- do not add new features
- do not expand models unless required for a fix
- treat regressions, deployment reliability, data safety, and test coverage as the main work

## Recommended Immediate Order

1. Move secrets out of `docker-compose.yml`
2. Rebuild and verify the fixed entrypoint on the server
3. Decide public vs private routes and adjust login gating
4. Run and document a real backup and restore drill
5. Expand route tests for critical user flows
