# Redis Commands

## Goal

Use these commands to inspect, debug, and operate the Redis service in this project.

## Connect

1. `docker compose exec redis redis-cli`
2. `docker compose exec redis redis-cli ping`
3. `docker compose exec redis redis-cli info`
4. `docker compose exec redis redis-cli info memory`
5. `docker compose exec redis redis-cli info keyspace`

Reason:

- These commands confirm the Redis container is reachable.
- They give a quick view of health, memory, and keyspace usage.

## Keys And Data

6. `docker compose exec redis redis-cli dbsize`
7. `docker compose exec redis redis-cli keys "*"`
8. `docker compose exec redis redis-cli scan 0`
9. `docker compose exec redis redis-cli get mykey`
10. `docker compose exec redis redis-cli set mykey hello`
11. `docker compose exec redis redis-cli del mykey`
12. `docker compose exec redis redis-cli exists mykey`
13. `docker compose exec redis redis-cli expire mykey 60`
14. `docker compose exec redis redis-cli ttl mykey`

Reason:

- These commands are useful for checking whether expected data exists.
- They cover common string key inspection and cleanup operations.

## Lists Sets Hashes

15. `docker compose exec redis redis-cli lpush mylist a b c`
16. `docker compose exec redis redis-cli lrange mylist 0 -1`
17. `docker compose exec redis redis-cli sadd myset one two three`
18. `docker compose exec redis redis-cli smembers myset`
19. `docker compose exec redis redis-cli hset myhash field1 value1`
20. `docker compose exec redis redis-cli hgetall myhash`
21. `docker compose exec redis redis-cli zadd myzset 1 one 2 two`
22. `docker compose exec redis redis-cli zrange myzset 0 -1 withscores`

Reason:

- These commands cover the main Redis data structures used in application debugging.
- They help verify queue-like, set-like, hash, and sorted-set behavior.

## Monitoring

23. `docker compose exec redis redis-cli monitor`
24. `docker compose exec redis redis-cli client list`
25. `docker compose exec redis redis-cli slowlog get 10`
26. `docker compose exec redis redis-cli config get "*"`
27. `docker compose logs -f redis`

Reason:

- These commands are useful when Redis is slow, busy, or behaving unexpectedly.
- They show live traffic, connected clients, slow operations, and runtime config.

## Maintenance

28. `docker compose exec redis redis-cli flushdb`
29. `docker compose exec redis redis-cli flushall`
30. `docker compose restart redis`
31. `docker compose stop redis`
32. `docker compose start redis`

Reason:

- These commands are for reset and service lifecycle operations.
- Use `flushdb` and `flushall` carefully because they delete data.
