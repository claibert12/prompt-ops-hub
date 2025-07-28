#!/usr/bin/env python3
"""
Script to check for skipped or xfail tests.
Fails if any @pytest.mark.skip or @pytest.mark.xfail decorators are found.
"""

import os
import re
import sys
from pathlib import Path


def check_file_for_skips(file_path: Path) -> list[str]:
    """Check a single file for skip/xfail markers.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        List of lines containing skip/xfail markers
    """
    violations = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if re.search(r'@pytest\.mark\.(skip|xfail)', line):
                    violations.append(f"{file_path}:{line_num}: {line}")
    except Exception as e:
        violations.append(f"{file_path}: Error reading file: {e}")
    
    return violations


def check_directory_for_skips(directory: str = "tests") -> list[str]:
    """Check all Python files in a directory for skip/xfail markers.
    
    Args:
        directory: Directory to check (default: tests)
        
    Returns:
        List of all violations found
    """
    violations = []
    test_dir = Path(directory)
    
    if not test_dir.exists():
        print(f"Warning: Directory {directory} does not exist")
        return violations
    
    for file_path in test_dir.rglob("*.py"):
        file_violations = check_file_for_skips(file_path)
        violations.extend(file_violations)
    
    return violations


def main() -> int:
    """Main function to check for skip/xfail markers.
    
    Returns:
        Exit code (0 for success, 1 for violations found)
    """
    print("🔍 Checking for skipped or xfail tests...")
    
    violations = check_directory_for_skips()
    
    if violations:
        print("❌ Found skip/xfail markers:")
        for violation in violations:
            print(f"  {violation}")
        print(f"\nTotal violations: {len(violations)}")
        return 1
    else:
        print("✅ No skip/xfail markers found")
        return 0


if __name__ == "__main__":
    sys.exit(main()) 