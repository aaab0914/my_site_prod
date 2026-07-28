        -- Slowest audit log requests
        -- Run from the server project root:
        --   cd /var/www/my_site_prod_repo_new
        --   docker compose -f docker-compose.prod.yml exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f -' < database_commands/<this-file>

        SELECT id, method, path, status_code, response_time, timestamp
FROM blog_auditlog
ORDER BY response_time DESC, timestamp DESC
LIMIT 10;
