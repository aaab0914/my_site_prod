# 30 Common Python Shell Commands

1. Print text
```python
print("hello")
```

2. Check the type of a value
```python
type(123)
```

3. Get help for an object
```python
help(str)
```

4. Import a standard library module
```python
import os
```

5. Show current working directory
```python
import os; os.getcwd()
```

6. List files in the current directory
```python
import os; os.listdir(".")
```

7. Check Python version from inside the shell
```python
import sys; sys.version
```

8. Show the executable path
```python
import sys; sys.executable
```

9. Show import search paths
```python
import sys; sys.path
```

10. Create a list
```python
numbers = [1, 2, 3, 4, 5]
```

11. Use list comprehension
```python
[n * 2 for n in numbers]
```

12. Create a dictionary
```python
user = {"name": "admin", "active": True}
```

13. Read a dictionary value
```python
user["name"]
```

14. Use sorted()
```python
sorted([5, 2, 9, 1])
```

15. Join strings
```python
", ".join(["a", "b", "c"])
```

16. Work with pathlib
```python
from pathlib import Path
```

17. Read a text file
```python
Path("README.md").read_text(encoding="utf-8")
```

18. Write a text file
```python
Path("sample.txt").write_text("hello", encoding="utf-8")
```

19. Check whether a path exists
```python
Path("README.md").exists()
```

20. Get current datetime
```python
import datetime; datetime.datetime.now()
```

21. Create a set
```python
unique_values = {1, 2, 3}
```

22. Check membership
```python
2 in unique_values
```

23. Enumerate a list
```python
list(enumerate(["a", "b", "c"], start=1))
```

24. Zip two lists
```python
list(zip([1, 2], ["a", "b"]))
```

25. Use any()
```python
any([False, False, True])
```

26. Use all()
```python
all([True, True, True])
```

27. Inspect object attributes
```python
dir(str)
```

28. Pretty print complex data
```python
from pprint import pprint
```

29. Show environment variables
```python
import os; dict(list(os.environ.items())[:5])
```

30. Exit the Python shell
```python
exit()
```
