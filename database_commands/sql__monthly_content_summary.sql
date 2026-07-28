        -- Monthly content summary
        -- Run from the server project root:
        --   cd /var/www/my_site_prod_repo_new
        --   docker compose -f docker-compose.prod.yml exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f -' < database_commands/<this-file>

        SELECT 'posts' AS source, DATE_TRUNC('month', publish) AS month_start, COUNT(*) AS total
FROM blog_post
GROUP BY month_start
UNION ALL
SELECT 'comments' AS source, DATE_TRUNC('month', created) AS month_start, COUNT(*) AS total
FROM blog_comment
GROUP BY month_start
ORDER BY month_start DESC, source ASC
LIMIT 24;
