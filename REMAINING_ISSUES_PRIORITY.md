# Remaining Issues Priority

## P0

1. Move access control away from broad middleware allowlists and into view-level permissions where possible.
2. Verify the production stack end to end after startup: `db` health, `web` health, `nginx` proxy, `/blog/`, `/blog/create/`.
3. Complete a real backup and restore drill on non-production data.

## P1

1. Expand integration tests for `POST` flows, uploads, and restore-sensitive paths.
2. Finish environment separation for development vs production settings.
3. Remove any remaining deployment assumptions that depend on bind-mounted source code.
4. Validate that the new `docker-compose.prod.yml` path is the one used on the server.
5. Keep adding route tests for public pages and private user pages.

## P2

1. Add more route-specific access policy tests for user pages and public blog pages.
2. Add health/readiness endpoints if you want simpler monitoring.
3. Improve log handling so operational debugging has one clear primary source.
4. Consider splitting settings into `base`, `dev`, and `prod` only after the current stack is stable.

## Current Rule

- Do not add new product features until P0 is done.
- Treat regressions, deployability, and data safety as the active work.
