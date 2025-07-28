#!/usr/bin/env python3
"""
Guardrails check script for Prompt Ops Hub.
Validates code quality, security, and compliance rules.
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Tuple


def check_forbidden_imports() -> List[str]:
    """Check for forbidden imports."""
    errors = []
    
    # Check for core imports
    for root, dirs, files in os.walk("src"):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "from core." in content or "import core" in content:
                        errors.append(f"❌ {filepath}: Found forbidden 'core' import")
    
    return errors


def check_security_patterns() -> List[str]:
    """Check for security-sensitive patterns."""
    errors = []
    
    security_patterns = [
        (r"password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password"),
        (r"api_key\s*=\s*['\"][^'\"]+['\"]", "Hardcoded API key"),
        (r"secret\s*=\s*['\"][^'\"]+['\"]", "Hardcoded secret"),
        (r"eval\s*\(", "Dangerous eval() usage"),
        (r"(?<!\.)exec\s*\(", "Dangerous exec() usage"),  # Not session.exec()
        (r"__import__\s*\(", "Dangerous __import__ usage"),
    ]
    
    for root, dirs, files in os.walk("src"):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        for pattern, description in security_patterns:
                            if re.search(pattern, line, re.IGNORECASE):
                                errors.append(f"⚠️  {filepath}:{line_num}: {description}")
    
    return errors


def check_code_quality() -> List[str]:
    """Check for code quality issues."""
    errors = []
    
    # Check for TODO/FIXME without context
    for root, dirs, files in os.walk("src"):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        if re.search(r"#\s*(TODO|FIXME)(?!\s*\()", line):
                            errors.append(f"📝 {filepath}:{line_num}: TODO/FIXME without context")
    
    return errors


def check_file_structure() -> List[str]:
    """Check file structure and naming."""
    errors = []
    
    # Check for __pycache__ in src
    for root, dirs, files in os.walk("src"):
        if "__pycache__" in dirs:
            errors.append(f"🗂️  {root}: Found __pycache__ directory")
    
    return errors


def main() -> int:
    """Main guardrails check function."""
    print("🔍 Running Prompt Ops Hub guardrails check...")
    
    all_errors = []
    
    # Run all checks
    all_errors.extend(check_forbidden_imports())
    all_errors.extend(check_security_patterns())
    all_errors.extend(check_code_quality())
    all_errors.extend(check_file_structure())
    
    # Report results
    if all_errors:
        print("❌ Guardrails check failed!")
        print("\nIssues found:")
        for error in all_errors:
            print(f"  {error}")
        print(f"\nTotal issues: {len(all_errors)}")
        return 1
    else:
        print("✅ All guardrails checks passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main()) 