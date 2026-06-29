# GitHub Guide

This file contains practical GitHub CLI style operations for `my_site_prod-master`.

Project root:

```powershell
cd C:\Users\K1457\Downloads\Compressed\my_site_prod-master
```

These commands assume `gh` is installed and that this local repository is connected to a GitHub remote.

## Common GitHub Operations

1. Check GitHub CLI authentication status:

```powershell
gh auth status
```

2. Log in to GitHub CLI:

```powershell
gh auth login
```

3. Show repository info:

```powershell
gh repo view
```

4. Open the repository in browser:

```powershell
gh repo view --web
```

5. Show the default branch:

```powershell
gh repo view --json defaultBranchRef
```

6. Show open pull requests:

```powershell
gh pr list
```

7. Show closed pull requests:

```powershell
gh pr list --state closed
```

8. Show open issues:

```powershell
gh issue list
```

9. Show issue details:

```powershell
gh issue view 1
```

10. Open an issue in the browser:

```powershell
gh issue view 1 --web
```

11. Create a new issue:

```powershell
gh issue create --title "Stabilize production deployment" --body "Track deployment hardening work for my_site_prod-master."
```

12. List pull requests assigned to您:

```powershell
gh pr list --assignee @me
```

13. View one pull request:

```powershell
gh pr view 1
```

14. Open one pull request in browser:

```powershell
gh pr view 1 --web
```

15. Check out a pull request locally:

```powershell
gh pr checkout 1
```

16. Create a pull request from the current branch:

```powershell
gh pr create --fill
```

17. Create a pull request with custom title:

```powershell
gh pr create --title "Harden logging and deployment flow" --body "This PR improves settings separation, logging behavior, and deployment validation."
```

18. Show pull request checks:

```powershell
gh pr checks 1
```

19. Merge a pull request:

```powershell
gh pr merge 1 --merge
```

20. Rebase-merge a pull request:

```powershell
gh pr merge 1 --rebase
```

21. Squash-merge a pull request:

```powershell
gh pr merge 1 --squash
```

22. List workflow runs:

```powershell
gh run list
```

23. View one workflow run:

```powershell
gh run view
```

24. Watch a running workflow:

```powershell
gh run watch
```

25. Download workflow logs:

```powershell
gh run view --log
```

26. Re-run a failed workflow:

```powershell
gh run rerun <run-id>
```

27. List repository releases:

```powershell
gh release list
```

28. Create a release:

```powershell
gh release create v1.0.0 --title "v1.0.0" --notes "Initial stable deployment milestone."
```

29. List repository secrets metadata:

```powershell
gh secret list
```

30. Show repository web page for actions:

```powershell
gh repo view --web
```

## Notes

- If this repository is not connected to GitHub yet, `gh repo view` and PR commands will fail until a valid remote exists.
- Use GitHub operations only after confirming the correct remote with `git remote -v`.
