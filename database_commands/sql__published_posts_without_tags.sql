        -- Published posts without tags
        -- Run from the server project root:
        --   cd /var/www/my_site_prod_repo_new
        --   docker compose -f docker-compose.prod.yml exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f -' < database_commands/<this-file>

        SELECT p.id, p.title, p.slug, p.publish
FROM blog_post AS p
LEFT JOIN taggit_taggeditem AS ti
    ON ti.object_id = p.id AND ti.content_type_id = (
        SELECT id FROM django_content_type
        WHERE app_label = 'blog' AND model = 'post'
    )
WHERE p.status = 'PB' AND ti.id IS NULL
ORDER BY p.publish DESC
LIMIT 10;
