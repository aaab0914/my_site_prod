        -- Most used tags on blog posts
        -- Run from the server project root:
        --   cd /var/www/my_site_prod_repo_new
        --   docker compose -f docker-compose.prod.yml exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f -' < database_commands/<this-file>

        SELECT t.id, t.name, t.slug, COUNT(ti.id) AS post_count
FROM taggit_tag AS t
LEFT JOIN taggit_taggeditem AS ti ON ti.tag_id = t.id
GROUP BY t.id, t.name, t.slug
ORDER BY post_count DESC, t.name ASC
LIMIT 10;
