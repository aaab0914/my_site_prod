# 30 Common Codex CLI Commands

1. Start an interactive Codex session
```powershell
codex
```

2. Start a session with an initial prompt
```powershell
codex "Explain this repository"
```

3. Run Codex non-interactively
```powershell
codex exec "Summarize the current project"
```

4. Run a code review non-interactively
```powershell
codex review
```

5. Log in
```powershell
codex login
```

6. Log out
```powershell
codex logout
```

7. Resume the most recent session
```powershell
codex resume --last
```

8. Open the resume picker
```powershell
codex resume
```

9. Fork the most recent session
```powershell
codex fork --last
```

10. Archive a session
```powershell
codex archive <session-id>
```

11. Unarchive a session
```powershell
codex unarchive <session-id>
```

12. Delete a saved session
```powershell
codex delete <session-id>
```

13. Use a specific model
```powershell
codex --model o3
```

14. Use a config profile
```powershell
codex --profile myprofile
```

15. Override config values inline
```powershell
codex -c model=\"o3\" -c shell_environment_policy.inherit=all
```

16. Enable a feature flag
```powershell
codex --enable search
```

17. Disable a feature flag
```powershell
codex --disable search
```

18. Enable live web search
```powershell
codex --search
```

19. Use workspace-write sandbox
```powershell
codex --sandbox workspace-write
```

20. Set approval policy
```powershell
codex --ask-for-approval on-request
```

21. Change the working directory
```powershell
codex --cd G:\Projests\Python_Projects\my_site_prod-master
```

22. Add an extra writable directory
```powershell
codex --add-dir G:\Projests\scripts
```

23. Attach an image to the initial prompt
```powershell
codex --image .\screenshot.png "Describe this UI"
```

24. Generate shell completion scripts
```powershell
codex completion
```

25. Diagnose local installation
```powershell
codex doctor
```

26. Update Codex CLI
```powershell
codex update
```

27. Manage MCP servers
```powershell
codex mcp
```

28. Manage plugins
```powershell
codex plugin
```

29. Launch the desktop app
```powershell
codex app
```

30. Show CLI help
```powershell
codex --help
```
