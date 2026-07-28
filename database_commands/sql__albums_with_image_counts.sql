        -- Albums with image counts
        -- Run from the server project root:
        --   cd /var/www/my_site_prod_repo_new
        --   docker compose -f docker-compose.prod.yml exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f -' < database_commands/<this-file>

        SELECT a.id, a.title, COUNT(ai.id) AS image_count, a.created
FROM images_album AS a
LEFT JOIN images_albumimage AS ai ON ai.album_id = a.id
GROUP BY a.id, a.title, a.created
ORDER BY image_count DESC, a.created DESC
LIMIT 10;
