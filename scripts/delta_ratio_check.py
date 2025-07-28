#!/usr/bin/env python3
"""
Script to check test/code ratio in changes.
Warns if ratio is too low (configurable threshold).
"""

import re
import sys
import subprocess
from pathlib import Path
from typing import Dict, Tuple


def count_lines_in_file(file_path: str) -> int:
    """Count non-empty lines in a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        Number of non-empty lines
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return len([line for line in f if line.strip()])
    except Exception:
        return 0


def get_changed_files() -> Dict[str, int]:
    """Get changed files and their line counts.
    
    Returns:
        Dict mapping file paths to line counts
    """
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD~1", "--name-only"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0 or not result.stdout.strip():
            # Fallback to staged files
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                check=False
            )
        
        if result.returncode != 0 or not result.stdout.strip():
            return {}
        
        files = result.stdout.strip().split('\n')
        file_counts = {}
        
        for file_path in files:
            if file_path and Path(file_path).exists():
                file_counts[file_path] = count_lines_in_file(file_path)
        
        return file_counts
    
    except Exception:
        return {}


def categorize_files(file_counts: Dict[str, int]) -> Tuple[Dict[str, int], Dict[str, int]]:
    """Categorize files into source and test files.
    
    Args:
        file_counts: Dict mapping file paths to line counts
        
    Returns:
        Tuple of (source_files, test_files) dicts
    """
    source_files = {}
    test_files = {}
    
    for file_path, count in file_counts.items():
        if file_path.startswith('src/') and file_path.endswith('.py'):
            source_files[file_path] = count
        elif file_path.startswith('tests/') and file_path.endswith('.py'):
            test_files[file_path] = count
    
    return source_files, test_files


def calculate_ratio(source_files: Dict[str, int], test_files: Dict[str, int], 
                   min_ratio: float = 0.005) -> Tuple[float, str]:
    """Calculate test/code ratio and generate message.
    
    Args:
        source_files: Dict of source files and line counts
        test_files: Dict of test files and line counts
        min_ratio: Minimum acceptable ratio (default: 1 test file per 200 LOC)
        
    Returns:
        Tuple of (ratio, message)
    """
    total_source_lines = sum(source_files.values())
    total_test_files = len(test_files)
    
    if total_source_lines == 0:
        return 1.0, "No source code changes"
    
    if total_test_files == 0:
        return 0.0, f"No test files changed (source: {total_source_lines} LOC)"
    
    ratio = total_test_files / total_source_lines
    
    if ratio >= min_ratio:
        status = "✅"
    else:
        status = "⚠️"
    
    message = (
        f"{status} Test/Code ratio: {total_test_files} test files / "
        f"{total_source_lines} source LOC = {ratio:.4f} "
        f"(threshold: {min_ratio:.4f})"
    )
    
    return ratio, message


def main() -> int:
    """Main function to check test/code ratio.
    
    Returns:
        Exit code (0 for success, 1 for warning)
    """
    print("🔍 Checking test/code ratio...")
    
    # Get changed files
    file_counts = get_changed_files()
    
    if not file_counts:
        print("✅ No files changed")
        return 0
    
    print(f"Found {len(file_counts)} changed file(s)")
    
    # Categorize files
    source_files, test_files = categorize_files(file_counts)
    
    print(f"Source files: {len(source_files)}")
    print(f"Test files: {len(test_files)}")
    
    # Calculate ratio
    ratio, message = calculate_ratio(source_files, test_files)
    
    print(f"\n{message}")
    
    # Show details
    if source_files:
        print("\nSource files:")
        for file_path, count in source_files.items():
            print(f"  {file_path}: {count} LOC")
    
    if test_files:
        print("\nTest files:")
        for file_path, count in test_files.items():
            print(f"  {file_path}: {count} LOC")
    
    # Return warning if ratio is low
    if ratio < 0.005:
        print("\n💡 Consider adding more tests for the changed source code")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 