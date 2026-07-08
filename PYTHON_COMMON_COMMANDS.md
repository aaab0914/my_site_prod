# 30 Common Python Commands

1. Check Python version
```powershell
python --version
```

2. Start the Python interpreter
```powershell
python
```

3. Run a Python script
```powershell
python app.py
```

4. Run a module
```powershell
python -m http.server
```

5. Show installed packages
```powershell
python -m pip list
```

6. Install a package
```powershell
python -m pip install requests
```

7. Upgrade a package
```powershell
python -m pip install --upgrade requests
```

8. Uninstall a package
```powershell
python -m pip uninstall requests
```

9. Show package details
```powershell
python -m pip show requests
```

10. Freeze dependencies
```powershell
python -m pip freeze
```

11. Install from requirements.txt
```powershell
python -m pip install -r requirements.txt
```

12. Download packages without installing
```powershell
python -m pip download -r requirements.txt -d .\packages
```

13. Create a virtual environment
```powershell
python -m venv .venv
```

14. Activate a virtual environment in PowerShell
```powershell
.venv\Scripts\Activate.ps1
```

15. Deactivate the virtual environment
```powershell
deactivate
```

16. Run a one-line Python command
```powershell
python -c "print('hello')"
```

17. Run a multiline script from stdin
```powershell
@'
print("hello")
print("world")
'@ | python -
```

18. Compile all Python files in a directory
```powershell
python -m compileall .
```

19. Run the built-in unittest test discovery
```powershell
python -m unittest discover
```

20. Run pytest through Python
```powershell
python -m pytest
```

21. Format datetime or other quick checks
```powershell
python -c "import datetime; print(datetime.datetime.now())"
```

22. Check the Python executable path
```powershell
python -c "import sys; print(sys.executable)"
```

23. Check sys.path
```powershell
python -c "import sys; print(sys.path)"
```

24. Start a local web server on port 8000
```powershell
python -m http.server 8000
```

25. Run a ZIP application
```powershell
python myapp.pyz
```

26. Generate a requirements file
```powershell
python -m pip freeze > requirements.txt
```

27. Install packages from a local wheel directory
```powershell
python -m pip install --no-index --find-links .\packages -r requirements.txt
```

28. Check pip version
```powershell
python -m pip --version
```

29. Upgrade pip
```powershell
python -m pip install --upgrade pip
```

30. Show full Python help
```powershell
python --help
```
