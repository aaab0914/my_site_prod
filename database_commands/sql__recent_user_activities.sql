        -- Recent user activities
        -- Run from the server project root:
        --   cd /var/www/my_site_prod_repo_new
        --   docker compose -f docker-compose.prod.yml exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f -' < database_commands/<this-file>

        SELECT ua.id, u.username, ua.action, ua.ip_address, ua.timestamp
FROM users_useractivity AS ua
JOIN auth_user AS u ON u.id = ua.user_id
ORDER BY ua.timestamp DESC
LIMIT 20;
