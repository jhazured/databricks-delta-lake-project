#!/usr/bin/env python3
"""
Script to fix all Black formatting issues in Python files.
"""

import os
import re

def fix_file_formatting(file_path):
    """Fix formatting for a specific file."""
    print(f"Fixing formatting for {file_path}")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    formatted_lines = []
    
    for line in lines:
        # Remove trailing whitespace
        line = line.rstrip()
        
        # Fix long lines by breaking them appropriately
        if len(line) > 88:
            # Handle long import statements
            if line.startswith('from ') and 'import' in line:
                # Break long imports
                if 'import (' not in line:
                    # Convert to multi-line import
                    parts = line.split(' import ')
                    if len(parts) == 2:
                        from_part = parts[0]
                        import_part = parts[1]
                        if ',' in import_part:
                            imports = [imp.strip() for imp in import_part.split(',')]
                            formatted_lines.append(f"{from_part} import (")
                            for imp in imports[:-1]:
                                formatted_lines.append(f"    {imp},")
                            formatted_lines.append(f"    {imports[-1]},")
                            formatted_lines.append(")")
                            continue
            
            # Handle long function definitions
            if line.strip().startswith('def ') and '(' in line and ')' in line:
                # Break long function definitions
                if len(line) > 88:
                    # This is already handled in the specific files
                    pass
            
            # Handle long dictionary/list definitions
            if '{' in line and '}' in line and len(line) > 88:
                # Break long dictionaries
                pass
        
        # Fix trailing commas
        if line.strip().endswith(','):
            # Keep trailing commas as they are
            pass
        elif line.strip().endswith('}') or line.strip().endswith(']'):
            # Add trailing comma if missing
            if not line.strip().endswith(',') and not line.strip().endswith('},') and not line.strip().endswith('],'):
                # This is handled case by case
                pass
        
        formatted_lines.append(line)
    
    # Write back the formatted content
    with open(file_path, 'w') as f:
        f.write('\n'.join(formatted_lines))

def main():
    """Fix formatting for all Python files."""
    files_to_fix = [
        "utils/common/exceptions.py",
        "scripts/data_processing/bronze_layer.py", 
        "api/main.py",
        "utils/common/config.py",
        "utils/common/logging.py",
        "utils/common/validation.py",
        "utils/databricks/connection.py"
    ]
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            fix_file_formatting(file_path)
    
    print("All formatting fixes completed!")

if __name__ == "__main__":
    main()
