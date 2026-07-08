# Git Guide

This file contains practical Git operations for `my_site_prod-master`.

Project root:

```powershell
cd G:\Projests\Python_Projects\my_site_prod-master
```

## Common Git Operations

1. Show current branch:

```powershell
git branch --show-current
```

2. Show working tree status:

```powershell
git status
```

3. Show short status:

```powershell
git status --short
```

4. Show changed files only:

```powershell
git diff --name-only
```

5. Show unstaged changes:

```powershell
git diff
```

6. Show staged changes:

```powershell
git diff --cached
```

7. Show changes for one file:

```powershell
git diff -- blog/views
```

8. Show commit history:

```powershell
git log --oneline --decorate --graph -20
```

9. Show recent commits affecting settings:

```powershell
git log --oneline -- my_site/settings
```

10. Show recent commits affecting compose files:

```powershell
git log --oneline -- docker-compose.yml docker-compose.prod.yml
```

11. Show one commit in detail:

```powershell
git show HEAD
```

12. Show one file at HEAD:

```powershell
git show HEAD:README.md
```

13. Stage one file:

```powershell
git add README.md
```

14. Stage multiple project files:

```powershell
git add my_site/tests/test_settings.py my_site/settings/dev.py
```

15. Stage all tracked and untracked changes:

```powershell
git add -A
```

16. Unstage one file:

```powershell
git restore --staged README.md
```

17. Commit staged changes:

```powershell
git commit -m "Stabilize logging and settings split"
```

18. Show remotes:

```powershell
git remote -v
```

19. Fetch latest remote refs:

```powershell
git fetch --all --prune
```

20. Compare current branch to origin:

```powershell
git status -sb
```

21. Show commits not yet pushed:

```powershell
git log --oneline origin/HEAD..HEAD
```

22. Create a new branch for infrastructure work:

```powershell
git switch -c chore/infrastructure-hardening
```

23. Switch back to an existing branch:

```powershell
git switch main
```

24. Rename current branch:

```powershell
git branch -m chore/logging-layout
```

25. Search history for a string:

```powershell
git log -S "docker-compose.prod.yml" --oneline
```

26. Show who last changed a line in a file:

```powershell
git blame my_site/settings/dev.py
```

27. Show changed files between two commits:

```powershell
git diff --name-only HEAD~1 HEAD
```

28. Stash current work:

```powershell
git stash push -m "temp before compose review"
```

29. List stashes:

```powershell
git stash list
```

30. Re-apply the latest stash:

```powershell
git stash pop
```

## Notes

- Avoid destructive Git commands unless您明确要这么做。
- This repo may contain local operational files, so always check `git status` before commit.
