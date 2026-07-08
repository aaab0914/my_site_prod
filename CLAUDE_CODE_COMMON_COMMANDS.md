# 30 Common Claude Code Commands

1. Start an interactive Claude Code session
```powershell
claude
```

2. Start a session with an initial prompt
```powershell
claude "Explain this repository"
```

3. Print a one-shot response and exit
```powershell
claude -p "Summarize the current directory"
```

4. Continue the most recent conversation
```powershell
claude -c
```

5. Resume a previous session
```powershell
claude -r
```

6. Resume a specific session by id
```powershell
claude --resume <session-id>
```

7. Resume and fork into a new session
```powershell
claude --resume <session-id> --fork-session
```

8. Use a specific model
```powershell
claude --model sonnet
```

9. Set effort level
```powershell
claude --effort high
```

10. Run in debug mode
```powershell
claude --debug
```

11. Write debug logs to a file
```powershell
claude --debug-file claude-debug.log
```

12. Add extra writable directories
```powershell
claude --add-dir G:\Projests\scripts
```

13. Use a custom session name
```powershell
claude --name repo-audit
```

14. Use a specific permission mode
```powershell
claude --permission-mode auto
```

15. Bypass permission prompts
```powershell
claude --dangerously-skip-permissions
```

16. Allow only selected tools
```powershell
claude --allowedTools "Bash Read Edit"
```

17. Disallow selected tools
```powershell
claude --disallowedTools "Bash(git push *)"
```

18. Use a custom system prompt
```powershell
claude --system-prompt "You are a senior Django reviewer."
```

19. Append extra system prompt text
```powershell
claude --append-system-prompt "Prefer short answers."
```

20. Print JSON output
```powershell
claude -p --output-format json "Return a summary"
```

21. Print stream JSON output
```powershell
claude -p --output-format stream-json "Analyze this codebase"
```

22. Use a JSON schema for structured output
```powershell
claude -p --output-format json --json-schema "{\"type\":\"object\",\"properties\":{\"summary\":{\"type\":\"string\"}},\"required\":[\"summary\"]}" "Summarize this repo"
```

23. Load extra settings from a file
```powershell
claude --settings .claude-settings.json
```

24. Use minimal bare mode
```powershell
claude --bare
```

25. Use a specific git worktree
```powershell
claude --worktree feature-audit
```

26. Check installation and updater health
```powershell
claude doctor
```

27. Manage authentication
```powershell
claude auth
```

28. List configured agents
```powershell
claude agents
```

29. Manage MCP servers
```powershell
claude mcp
```

30. Check for updates
```powershell
claude update
```
