        -- Comments carrying uploaded images
        -- Run from the server project root:
        --   cd /var/www/my_site_prod_repo_new
        --   docker compose -f docker-compose.prod.yml exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f -' < database_commands/<this-file>

        SELECT c.id, p.title AS post_title, u.username AS author, c.image, c.created
FROM blog_comment AS c
JOIN blog_post AS p ON p.id = c.post_id
JOIN auth_user AS u ON u.id = c.author_id
WHERE c.image IS NOT NULL AND c.image <> ''
ORDER BY c.created DESC
LIMIT 10;
