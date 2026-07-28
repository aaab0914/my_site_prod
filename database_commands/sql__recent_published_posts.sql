        -- Recent published blog posts
        -- Run from the server project root:
        --   cd /var/www/my_site_prod_repo_new
        --   docker compose -f docker-compose.prod.yml exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f -' < database_commands/<this-file>

        SELECT p.id, p.title, p.slug, u.username AS author, p.publish
FROM blog_post AS p
JOIN auth_user AS u ON u.id = p.author_id
WHERE p.status = 'PB'
ORDER BY p.publish DESC
LIMIT 10;
