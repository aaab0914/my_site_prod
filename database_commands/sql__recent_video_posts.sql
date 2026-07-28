        -- Recent video uploads
        -- Run from the server project root:
        --   cd /var/www/my_site_prod_repo_new
        --   docker compose -f docker-compose.prod.yml exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f -' < database_commands/<this-file>

        SELECT v.id, v.title, u.username AS uploaded_by, v.created
FROM blog_videopost AS v
JOIN auth_user AS u ON u.id = v.uploaded_by_id
ORDER BY v.created DESC
LIMIT 10;
