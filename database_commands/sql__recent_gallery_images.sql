        -- Recent gallery image uploads
        -- Run from the server project root:
        --   cd /var/www/my_site_prod_repo_new
        --   docker compose -f docker-compose.prod.yml exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f -' < database_commands/<this-file>

        SELECT i.id, i.title, u.username AS uploaded_by, i.created
FROM images_imagepost AS i
JOIN auth_user AS u ON u.id = i.uploaded_by_id
ORDER BY i.created DESC
LIMIT 10;
