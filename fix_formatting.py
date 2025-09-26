#!/usr/bin/env python3
"""
Script to fix formatting issues in Python files.
"""

import subprocess
import sys
import os

def fix_formatting():
    """Fix formatting issues in Python files."""
    
    # Files that need formatting fixes
    files_to_fix = [
        "utils/common/__init__.py",
        "utils/common/exceptions.py", 
        "utils/common/config.py",
        "utils/common/validation.py",
        "utils/databricks/__init__.py",
        "utils/databricks/connection.py",
        "scripts/data_processing/bronze_layer.py",
        "api/main.py",
        "utils/common/logging.py"
    ]
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            print(f"Fixing formatting for {file_path}")
            
            # Read the file
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Apply basic formatting fixes
            lines = content.split('\n')
            formatted_lines = []
            
            for line in lines:
                # Remove trailing whitespace
                line = line.rstrip()
                # Fix common formatting issues
                if line.endswith(','):
                    # Keep trailing commas as they are
                    pass
                elif line.strip() and not line.startswith('#'):
                    # Ensure proper spacing around operators
                    line = line.replace(' = ', ' = ').replace('= ', '= ').replace(' =', ' =')
                
                formatted_lines.append(line)
            
            # Write back the formatted content
            with open(file_path, 'w') as f:
                f.write('\n'.join(formatted_lines))
            
            print(f"Fixed formatting for {file_path}")

if __name__ == "__main__":
    fix_formatting()
    print("Formatting fixes completed!")
