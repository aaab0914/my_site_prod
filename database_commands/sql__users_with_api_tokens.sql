        -- Users holding DRF auth tokens
        -- Run from the server project root:
        --   cd /var/www/my_site_prod_repo_new
        --   docker compose -f docker-compose.prod.yml exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f -' < database_commands/<this-file>

        SELECT u.username, t.created
FROM authtoken_token AS t
JOIN auth_user AS u ON u.id = t.user_id
ORDER BY u.username ASC
LIMIT 20;
