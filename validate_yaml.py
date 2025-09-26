#!/usr/bin/env python3
"""Validate YAML syntax for Kubernetes manifests."""
import yaml
import sys
import os

def validate_yaml_file(file_path):
    """Validate YAML syntax of a file."""
    try:
        with open(file_path, 'r') as f:
            yaml.safe_load_all(f)
        print(f'✅ YAML syntax is valid: {file_path}')
        return True
    except yaml.YAMLError as e:
        print(f'❌ YAML syntax error in {file_path}: {e}')
        return False
    except Exception as e:
        print(f'❌ Error reading file {file_path}: {e}')
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validate_yaml.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    if not validate_yaml_file(file_path):
        sys.exit(1)
