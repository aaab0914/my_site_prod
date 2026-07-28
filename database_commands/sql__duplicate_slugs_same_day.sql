        -- Duplicate slugs on the same publish day
        -- Run from the server project root:
        --   cd /var/www/my_site_prod_repo_new
        --   docker compose -f docker-compose.prod.yml exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f -' < database_commands/<this-file>

        SELECT slug, DATE(publish) AS publish_day, COUNT(*) AS row_count
FROM blog_post
GROUP BY slug, DATE(publish)
HAVING COUNT(*) > 1
ORDER BY row_count DESC, slug ASC
LIMIT 10;
