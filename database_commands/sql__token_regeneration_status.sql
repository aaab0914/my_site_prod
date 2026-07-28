        -- Token regeneration cooldown status
        -- Run from the server project root:
        --   cd /var/www/my_site_prod_repo_new
        --   docker compose -f docker-compose.prod.yml exec -T db sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f -' < database_commands/<this-file>

        SELECT u.username,
       u.is_staff,
       p.last_token_generated_at,
       GREATEST(
           0,
           5 - FLOOR(EXTRACT(EPOCH FROM (NOW() - p.last_token_generated_at)) / 86400)
       ) AS remaining_days
FROM users_profile AS p
JOIN auth_user AS u ON u.id = p.user_id
ORDER BY u.username ASC
LIMIT 20;
