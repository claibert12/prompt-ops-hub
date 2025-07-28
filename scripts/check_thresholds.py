#!/usr/bin/env python3
"""
Script to check coverage thresholds and prevent lowering.
Fails if coverage threshold is <80% or was lowered in this PR.
"""

import sys
from integrity_core import CoverageChecker


def main() -> int:
    """Main function to check coverage thresholds.
    
    Returns:
        Exit code (0 for success, 1 for violations)
    """
    print("Checking coverage thresholds...")
    
    checker = CoverageChecker()
    success, violations = checker.check()
    
    if not success:
        print("\n❌ Coverage threshold violations:")
        for violation in violations:
            print(f"  {violation}")
        return 1
    else:
        print("\nAll coverage thresholds meet integrity requirements")
        return 0


if __name__ == "__main__":
    sys.exit(main()) 