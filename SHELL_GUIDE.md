# Shell Guide

This file contains useful PowerShell and shell-style operations for `my_site_prod-master`.

Project root:

```powershell
cd G:\Projests\Python_Projects\my_site_prod-master
```

## Common Shell Operations

1. Show current directory:

```powershell
Get-Location
```

2. List root files:

```powershell
Get-ChildItem
```

3. List hidden files too:

```powershell
Get-ChildItem -Force
```

4. List only Markdown docs:

```powershell
Get-ChildItem *.md
```

5. Search for all test files:

```powershell
Get-ChildItem -Recurse -Filter *tests*.py
```

6. Search for all compose files:

```powershell
Get-ChildItem -Recurse -Filter docker-compose*.yml
```

7. Read README:

```powershell
Get-Content .\README.md
```

8. Read the last 50 lines of README:

```powershell
Get-Content .\README.md -Tail 50
```

9. Search for `DJANGO_SETTINGS_MODULE`:

```powershell
Get-ChildItem -Recurse | Select-String -Pattern "DJANGO_SETTINGS_MODULE"
```

10. Search for `docker-compose.prod.yml` references:

```powershell
Get-ChildItem -Recurse | Select-String -Pattern "docker-compose.prod.yml"
```

11. List logs root:

```powershell
Get-ChildItem .\logs
```

12. List current month log directory:

```powershell
Get-ChildItem .\logs\2026-06
```

13. Read current daily Django log:

```powershell
Get-Content .\logs\2026-06\django-2026-06-25.log -Tail 100
```

14. Read current daily error log:

```powershell
Get-Content .\logs\2026-06\error-2026-06-25.log -Tail 100
```

15. List backup files:

```powershell
Get-ChildItem .\backups\db
```

16. Sort backups by newest:

```powershell
Get-ChildItem .\backups\db | Sort-Object LastWriteTime -Descending
```

17. List media files recursively:

```powershell
Get-ChildItem .\media -Recurse
```

18. List staticfiles recursively:

```powershell
Get-ChildItem .\staticfiles -Recurse
```

19. Check entrypoint script:

```powershell
Get-Content .\entrypoint.sh
```

20. Check Dockerfile:

```powershell
Get-Content .\Dockerfile
```

21. Check production compose file:

```powershell
Get-Content .\docker-compose.prod.yml
```

22. Check development compose file:

```powershell
Get-Content .\docker-compose.yml
```

23. Show file sizes in the project root:

```powershell
Get-ChildItem | Select-Object Name, Length
```

24. Show the largest files under media:

```powershell
Get-ChildItem .\media -Recurse | Sort-Object Length -Descending | Select-Object -First 20 FullName, Length
```

25. Create a timestamp string for notes:

```powershell
Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
```

26. Show environment variables related to database:

```powershell
Get-ChildItem Env: | Where-Object { $_.Name -like "DB_*" }
```

27. Show environment variables related to Django:

```powershell
Get-ChildItem Env: | Where-Object { $_.Name -like "*DJANGO*" }
```

28. Search for all `.sh` scripts:

```powershell
Get-ChildItem -Recurse -Filter *.sh
```

29. Search for all test docs:

```powershell
Get-ChildItem -Recurse -Filter *GUIDE.md
```

30. Read the production verification checklist:

```powershell
Get-Content .\PRODUCTION_VERIFICATION.md
```
