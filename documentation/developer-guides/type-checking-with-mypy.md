# Type Checking with mypy

## Overview

mypy is a static type checker for Python that helps catch type-related errors before runtime. It enforces type safety, improves code quality, and provides better IDE support.

## Table of Contents

- [Installation and Setup](#installation-and-setup)
- [Common mypy Errors and Solutions](#common-mypy-errors-and-solutions)
- [Type Annotation Best Practices](#type-annotation-best-practices)
- [Running mypy](#running-mypy)
- [Configuration](#configuration)
- [Integration with CI/CD](#integration-with-cicd)

## Installation and Setup

### Install mypy

```bash
# Install mypy
pip install mypy

# Install type stubs for common libraries
pip install types-PyYAML types-requests types-urllib3
```

### Install Type Stubs

Type stubs provide type information for libraries that don't have built-in type hints:

```bash
# Common type stubs
pip install types-PyYAML      # For yaml library
pip install types-requests    # For requests library
pip install types-urllib3     # For urllib3 library
pip install pandas-stubs      # For pandas library
pip install types-FastAPI     # For FastAPI (if needed)
```

## Common mypy Errors and Solutions

### 1. Library Stubs Not Installed (`import-untyped`)

**Error:**
```
utils/common/config.py:12: error: Library stubs not installed for "yaml"  [import-untyped]
utils/databricks/connection.py:8: error: Library stubs not installed for "requests"  [import-untyped]
```

**What it means:**
- mypy couldn't find type information for external libraries
- These libraries don't have built-in type hints, so mypy needs separate "stub" files
- Stub files (`.pyi`) contain type information for libraries written in C or without type hints

**Why it matters:**
- Without stubs, mypy can't check if you're using the library correctly
- You might pass wrong types to functions and not catch the error until runtime

**Solution:**
```bash
# Install the appropriate type stubs
pip install types-PyYAML types-requests
```

### 2. Missing Return Type Annotations (`no-untyped-def`)

**Error:**
```
api/main.py:70: error: Function is missing a return type annotation  [no-untyped-def]
api/main.py:84: error: Function is missing a return type annotation  [no-untyped-def]
```

**What it means:**
- Functions didn't specify what type they return
- mypy couldn't verify that callers handle the return value correctly

**Why it matters:**
- **Type Safety**: Ensures functions return what callers expect
- **Documentation**: Makes code self-documenting
- **IDE Support**: Better autocomplete and error detection
- **Refactoring**: Safer code changes

**Solution:**
```python
# Before (no return type)
async def health_check(config: Dict[str, Any] = Depends(get_app_config)):
    return HealthResponse(...)

# After (with return type)
async def health_check(config: Dict[str, Any] = Depends(get_app_config)) -> HealthResponse:
    return HealthResponse(...)
```

### 3. Missing Argument Type Annotations

**Error:**
```
api/main.py:84: error: Function is missing a type annotation for one or more arguments  [no-untyped-def]
```

**What it means:**
- Function parameters didn't have type hints
- mypy couldn't verify that callers pass the right types

**Why it matters:**
- **Input Validation**: Catches type mismatches before runtime
- **API Contracts**: Makes function interfaces clear
- **Error Prevention**: Prevents bugs from wrong argument types

**Solution:**
```python
# Before (no argument types)
async def delta_lake_error_handler(request, exc: DeltaLakeError):

# After (with argument types)
async def delta_lake_error_handler(request: Request, exc: DeltaLakeError) -> JSONResponse:
```

### 4. Incompatible Types

**Error:**
```
utils/common/validation.py:45: error: Incompatible types in assignment (expression has type "str", variable has type "Path")
```

**What it means:**
- You're trying to assign a value of one type to a variable expecting another type
- mypy detected a type mismatch that could cause runtime errors

**Solution:**
```python
# Before (type mismatch)
output_path = Path(output_path)  # output_path is str, but Path() expects str
output_path = "new_string"       # Error: can't assign str to Path

# After (correct types)
output_path_str = output_path    # Keep original as str
output_dir = Path(output_path_str)  # Create Path object separately
```

### 5. Missing Return Statement

**Error:**
```
api/main.py:308: note: Use "-> None" if function does not return a value
```

**What it means:**
- Function doesn't return anything but mypy expects a return type annotation
- Use `-> None` to explicitly indicate the function returns nothing

**Solution:**
```python
# Before (missing return type)
async def startup_event():
    """Application startup event."""
    # ... code that doesn't return anything

# After (with None return type)
async def startup_event() -> None:
    """Application startup event."""
    # ... code that doesn't return anything
```

## Type Annotation Best Practices

### Basic Types

```python
def func() -> str:           # Returns string
def func() -> int:           # Returns integer
def func() -> None:          # Returns nothing (void)
def func() -> bool:          # Returns boolean
```

### Collections

```python
from typing import List, Dict, Any, Optional, Union

def func() -> List[str]:                    # Returns list of strings
def func() -> Dict[str, Any]:               # Returns dictionary
def func() -> Optional[str]:                # Returns string or None
def func() -> Union[str, int]:              # Returns string or integer
def func() -> List[Dict[str, Any]]:         # Returns list of dictionaries
```

### Complex Types

```python
from fastapi import JSONResponse
from pydantic import BaseModel

def func() -> JSONResponse:                 # Returns FastAPI response
def func() -> HealthResponse:               # Returns Pydantic model
def func() -> Tuple[str, int]:              # Returns tuple
```

### Function Parameters

```python
def process_data(data: List[Dict[str, Any]], 
                config: Optional[Dict[str, str]] = None) -> bool:
    """Process data with optional configuration."""
    return True
```

### Class Methods

```python
class DataProcessor:
    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
    
    def process(self, data: List[str]) -> List[Dict[str, Any]]:
        """Process list of strings into list of dictionaries."""
        return [{"item": item} for item in data]
```

## Running mypy

### Basic Usage

```bash
# Check specific files
mypy utils/ scripts/ api/

# Check with missing imports ignored
mypy utils/ scripts/ api/ --ignore-missing-imports

# Check specific file
mypy api/main.py

# Check with strict mode
mypy --strict utils/
```

### Common Options

```bash
# Ignore missing imports (useful for external libraries)
mypy --ignore-missing-imports .

# Show error codes
mypy --show-error-codes .

# Follow imports
mypy --follow-imports=silent .

# Check untyped definitions
mypy --disallow-untyped-defs .
```

## Configuration

### mypy.ini Configuration

Create a `mypy.ini` file in your project root:

```ini
[mypy]
python_version = 3.9
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
disallow_incomplete_defs = True
check_untyped_defs = True
disallow_untyped_decorators = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
warn_no_return = True
warn_unreachable = True
strict_equality = True

# Ignore missing imports for specific modules
[mypy-pandas.*]
ignore_missing_imports = True

[mypy-numpy.*]
ignore_missing_imports = True
```

### pyproject.toml Configuration

Add mypy configuration to your `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[[tool.mypy.overrides]]
module = ["pandas.*", "numpy.*"]
ignore_missing_imports = true
```

## Integration with CI/CD

### GitHub Actions

Our CI/CD pipeline includes mypy checking:

```yaml
- name: Type Checking
  run: |
    mypy utils/ scripts/ api/ --ignore-missing-imports
```

### Pre-commit Hooks

Add mypy to your pre-commit configuration:

```yaml
repos:
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
        additional_dependencies: [types-PyYAML, types-requests]
```

## Benefits of Type Checking

### 1. Runtime vs Compile-time Safety
- **Without type hints**: Errors only discovered when code runs
- **With type hints**: Errors caught during development/CI

### 2. Code Quality
- **Self-documenting**: Types serve as inline documentation
- **Maintainability**: Easier to understand and modify code
- **Team Collaboration**: Clear contracts between functions

### 3. IDE Benefits
- **Autocomplete**: Better suggestions based on types
- **Error Highlighting**: Immediate feedback on type mismatches
- **Refactoring**: Safer renaming and restructuring

### 4. CI/CD Integration
- **Automated Checks**: mypy runs in GitHub Actions
- **Quality Gates**: Prevents merging code with type issues
- **Consistency**: Enforces type safety across the team

## Troubleshooting

### Common Issues

1. **Import Errors**: Install missing type stubs
2. **Complex Types**: Use `Any` for complex or dynamic types
3. **Third-party Libraries**: Use `# type: ignore` for problematic imports
4. **Legacy Code**: Gradually add types, don't try to type everything at once

### Useful Commands

```bash
# Install all missing type stubs
mypy --install-types

# Check what stubs are available
pip search types-

# Generate stub files for your own modules
stubgen -p your_module
```

## Resources

- [mypy Documentation](https://mypy.readthedocs.io/)
- [Python Type Hints Guide](https://docs.python.org/3/library/typing.html)
- [FastAPI Type Hints](https://fastapi.tiangolo.com/python-types/)
- [Pydantic Type Hints](https://pydantic-docs.helpmanual.io/usage/types/)

## Summary

Type checking with mypy provides:

- ✅ **Early Error Detection**: Catch type-related bugs before runtime
- ✅ **Better Code Quality**: Self-documenting, maintainable code
- ✅ **IDE Support**: Enhanced autocomplete and error highlighting
- ✅ **Team Productivity**: Clear interfaces and safer refactoring
- ✅ **CI/CD Integration**: Automated quality gates

Start with basic type annotations and gradually add more sophisticated types as you become comfortable with the tool.
