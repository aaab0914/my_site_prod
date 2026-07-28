        -- Album images not linked to an album
        -- Run from the server project root:
        --   cd /var/www/my_site_prod_repo_new
        --   docker compose -f docker-compose.prod.yml exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f -' < database_commands/<this-file>

        SELECT ai.id, ai.title, u.username AS uploaded_by, ai.created
FROM images_albumimage AS ai
JOIN auth_user AS u ON u.id = ai.uploaded_by_id
WHERE ai.album_id IS NULL
ORDER BY ai.created DESC
LIMIT 10;
