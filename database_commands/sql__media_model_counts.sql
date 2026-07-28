        -- Counts across content models
        -- Run from the server project root:
        --   cd /var/www/my_site_prod_repo_new
        --   docker compose -f docker-compose.prod.yml exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f -' < database_commands/<this-file>

        SELECT 'posts' AS model_name, COUNT(*) AS row_count FROM blog_post
UNION ALL
SELECT 'comments', COUNT(*) FROM blog_comment
UNION ALL
SELECT 'audio_posts', COUNT(*) FROM blog_audiopost
UNION ALL
SELECT 'video_posts', COUNT(*) FROM blog_videopost
UNION ALL
SELECT 'gallery_images', COUNT(*) FROM images_imagepost
UNION ALL
SELECT 'albums', COUNT(*) FROM images_album
UNION ALL
SELECT 'album_images', COUNT(*) FROM images_albumimage
ORDER BY model_name;
