# 30 Common Docker Commands

## Images

1. List local images
```powershell
docker images
```

2. Pull an image
```powershell
docker pull nginx:1.25
```

3. Remove an image
```powershell
docker rmi nginx:1.25
```

4. Export an image to a tar file
```powershell
docker save -o nginx_1.25.tar nginx:1.25
```

5. Import an image from a tar file
```powershell
docker load -i .\nginx_1.25.tar
```

## Containers

6. List running containers
```powershell
docker ps
```

7. List all containers
```powershell
docker ps -a
```

8. Start a container
```powershell
docker start my_container
```

9. Stop a container
```powershell
docker stop my_container
```

10. Restart a container
```powershell
docker restart my_container
```

11. Remove a container
```powershell
docker rm my_container
```

12. Force remove a container
```powershell
docker rm -f my_container
```

13. Inspect a container
```powershell
docker inspect my_container
```

14. View container resource usage
```powershell
docker stats
```

15. View container logs
```powershell
docker logs my_container
```

16. Follow container logs
```powershell
docker logs -f my_container
```

17. Show only the last 100 log lines
```powershell
docker logs --tail 100 my_container
```

18. Open a shell inside a container
```powershell
docker exec -it my_container sh
```

19. Run a single command inside a container
```powershell
docker exec my_container ls /app
```

20. Copy a file into a container
```powershell
docker cp .\local.txt my_container:/tmp/local.txt
```

21. Copy a file out of a container
```powershell
docker cp my_container:/tmp/local.txt .\local.txt
```

## Run And Build

22. Run a temporary container
```powershell
docker run --rm nginx:1.25
```

23. Run a container in the background with port mapping
```powershell
docker run -d --name my_nginx -p 8080:80 nginx:1.25
```

24. Build an image locally
```powershell
docker build -t my_site_prod-master-web .
```

25. Build an image without cache
```powershell
docker build --no-cache -t my_site_prod-master-web .
```

## Compose

26. Start compose services
```powershell
docker compose up -d
```

27. Stop compose services
```powershell
docker compose down
```

28. View compose service status
```powershell
docker compose ps
```

29. Build compose services
```powershell
docker compose build
```

30. View compose service logs
```powershell
docker compose logs -f
```
