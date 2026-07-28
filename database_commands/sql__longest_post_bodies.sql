        -- Posts with the longest bodies
        -- Run from the server project root:
        --   cd /var/www/my_site_prod_repo_new
        --   docker compose -f docker-compose.prod.yml exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f -' < database_commands/<this-file>

        SELECT id, title, LENGTH(body) AS body_length, publish
FROM blog_post
ORDER BY body_length DESC, publish DESC
LIMIT 10;
