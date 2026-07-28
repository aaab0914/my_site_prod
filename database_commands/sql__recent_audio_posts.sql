        -- Recent audio uploads
        -- Run from the server project root:
        --   cd /var/www/my_site_prod_repo_new
        --   docker compose -f docker-compose.prod.yml exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f -' < database_commands/<this-file>

        SELECT a.id, a.music_name, u.username AS uploaded_by, a.active, a.created
FROM blog_audiopost AS a
JOIN auth_user AS u ON u.id = a.uploaded_by_id
ORDER BY a.created DESC
LIMIT 10;
