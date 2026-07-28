        -- Most requested paths in audit logs
        -- Run from the server project root:
        --   cd /var/www/my_site_prod_repo_new
        --   docker compose -f docker-compose.prod.yml exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f -' < database_commands/<this-file>

        SELECT path, COUNT(*) AS hit_count
FROM blog_auditlog
GROUP BY path
ORDER BY hit_count DESC, path ASC
LIMIT 20;
