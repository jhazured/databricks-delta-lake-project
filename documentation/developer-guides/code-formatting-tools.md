# Code Formatting Tools Guide

This guide explains the code formatting and quality tools used in the Databricks Delta Lake project.

## Overview

We use two main tools for maintaining code quality and consistency:

- **Black** - Python code formatter
- **isort** - Import statement organizer

Both tools are integrated into our CI/CD pipeline and run automatically on every commit.

## Black - Python Code Formatter

### What is Black?

Black is an opinionated Python code formatter that automatically formats your code to follow a consistent style. It's called "The Uncompromising Code Formatter" because it makes formatting decisions for you.

### Key Features

- **Automatic formatting** - No configuration needed
- **Consistent style** - Same formatting across all files
- **PEP 8 compliant** - Follows Python style guidelines
- **Fast** - Quick formatting of large codebases
- **Integration** - Works with IDEs and CI/CD

### Black Configuration

Our project uses Black with these settings (in `pyproject.toml`):

```toml
[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''
```

### How Black Works

#### Before Black:
```python
def process_data(data,config,debug=False):
    if debug:
        print(f"Processing {len(data)} records")
    result=[]
    for item in data:
        if item['status']=='active':
            result.append({
                'id':item['id'],
                'name':item['name'],
                'processed_at':datetime.now()
            })
    return result
```

#### After Black:
```python
def process_data(data, config, debug=False):
    if debug:
        print(f"Processing {len(data)} records")
    result = []
    for item in data:
        if item["status"] == "active":
            result.append(
                {
                    "id": item["id"],
                    "name": item["name"],
                    "processed_at": datetime.now(),
                }
            )
    return result
```

### Black Commands

```bash
# Check if code is formatted correctly
black --check utils/ scripts/ api/

# Format code
black utils/ scripts/ api/

# Format specific file
black utils/common/logging.py

# Show what would be changed (dry run)
black --diff utils/ scripts/ api/
```

## isort - Import Statement Organizer

### What is isort?

isort is a Python utility that automatically sorts and organizes import statements according to a consistent style. It groups imports logically and sorts them alphabetically.

### Key Features

- **Import grouping** - Organizes imports by type
- **Alphabetical sorting** - Sorts imports within groups
- **Duplicate removal** - Removes duplicate imports
- **Consistent style** - Same import format across files
- **Black compatibility** - Works seamlessly with Black

### isort Configuration

Our project uses isort with these settings (in `pyproject.toml`):

```toml
[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
```

### Import Groups (in order)

1. **Standard library imports** (built-in Python modules)
2. **Third-party imports** (installed packages)
3. **Local imports** (your project modules)

### How isort Works

#### Before isort:
```python
import os
from datetime import datetime
import pandas as pd
from .utils import helper
import sys
from typing import List
from databricks import sql
```

#### After isort:
```python
import os
import sys
from datetime import datetime
from typing import List

import pandas as pd
from databricks import sql

from .utils import helper
```

### isort Commands

```bash
# Check if imports are sorted correctly
isort --check-only utils/ scripts/ api/

# Sort imports
isort utils/ scripts/ api/

# Sort specific file
isort utils/common/logging.py

# Show what would be changed (dry run)
isort --diff utils/ scripts/ api/
```

## Integration with CI/CD

### GitHub Actions Workflow

Both tools are integrated into our CI/CD pipeline in the `code-quality` job:

```yaml
- name: Check code formatting with black
  run: |
    black --check utils/ scripts/ api/

- name: Check import sorting with isort
  run: |
    isort --check-only utils/ scripts/ api/
```

### What Happens in CI/CD

1. **Code Quality Job** runs on every commit
2. **Black check** validates code formatting
3. **isort check** validates import sorting
4. **Pipeline fails** if formatting issues are found
5. **Developer must fix** formatting before merge

## Local Development Setup

### Option 1: Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install tools
pip install black isort

# Format code
black utils/ scripts/ api/
isort utils/ scripts/ api/

# Check formatting
black --check utils/ scripts/ api/
isort --check-only utils/ scripts/ api/
```

### Option 2: IDE Integration

Most modern IDEs support Black and isort:

#### VS Code
- Install "Python" extension
- Install "Black Formatter" extension
- Install "isort" extension
- Configure to format on save

#### PyCharm
- Go to Settings → Tools → External Tools
- Add Black and isort as external tools
- Configure to run on file save

#### Vim/Neovim
- Use plugins like `vim-black` and `vim-isort`
- Configure to run on save

## Best Practices

### 1. Format Before Committing

Always format your code before committing:

```bash
# Format all Python files
black utils/ scripts/ api/
isort utils/ scripts/ api/

# Then commit
git add .
git commit -m "feat: add new feature"
```

### 2. Use IDE Integration

Configure your IDE to format on save to avoid manual formatting.

### 3. Check CI/CD Results

Always check the CI/CD pipeline results to ensure formatting passes.

### 4. Don't Fight the Tools

Black and isort make formatting decisions for you. Don't try to override them - embrace the consistency.

## Troubleshooting

### Common Issues

#### Black Formatting Issues

**Problem**: Black check fails in CI/CD
**Solution**: Run Black locally and commit the changes

```bash
black utils/ scripts/ api/
git add .
git commit -m "fix: apply Black formatting"
```

#### isort Import Issues

**Problem**: isort check fails in CI/CD
**Solution**: Run isort locally and commit the changes

```bash
isort utils/ scripts/ api/
git add .
git commit -m "fix: apply isort import sorting"
```

#### Conflicting Formatting

**Problem**: Black and isort produce conflicting results
**Solution**: Use isort with Black profile (already configured)

```toml
[tool.isort]
profile = "black"
```

### Getting Help

- **Black Documentation**: https://black.readthedocs.io/
- **isort Documentation**: https://pycqa.github.io/isort/
- **Project Issues**: Create GitHub issue for project-specific problems

## Configuration Files

### pyproject.toml

Our complete configuration:

```toml
[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311']
include = '\.pyi?$'

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true
```

## Summary

- **Black** ensures consistent code formatting
- **isort** ensures consistent import organization
- Both tools run automatically in CI/CD
- Format code before committing
- Use IDE integration for best experience
- Don't fight the tools - embrace consistency

These tools help maintain high code quality and consistency across the entire project, making it easier for all developers to read and maintain the codebase.
