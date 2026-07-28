        -- Posts with comment counts
        -- Run from the server project root:
        --   cd /var/www/my_site_prod_repo_new
        --   docker compose -f docker-compose.prod.yml exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f -' < database_commands/<this-file>

        SELECT p.id, p.title, COUNT(c.id) AS comment_count
FROM blog_post AS p
LEFT JOIN blog_comment AS c ON c.post_id = p.id
GROUP BY p.id, p.title
ORDER BY comment_count DESC, MAX(p.publish) DESC
LIMIT 10;
