        -- Users without preferences rows
        -- Run from the server project root:
        --   cd /var/www/my_site_prod_repo_new
        --   docker compose -f docker-compose.prod.yml exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f -' < database_commands/<this-file>

        SELECT u.id, u.username, u.email
FROM auth_user AS u
LEFT JOIN users_userpreference AS up ON up.user_id = u.id
WHERE up.id IS NULL
ORDER BY u.id ASC
LIMIT 20;
