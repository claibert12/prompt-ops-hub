#!/usr/bin/env python3
"""
Script to detect test tampering without proper markers.
Fails if tests/ or CI/coverage configs changed without #TEST_CHANGE marker.
"""

import sys
from integrity_core import TamperChecker


def main() -> int:
    """Main function to check for test tampering.
    
    Returns:
        Exit code (0 for success, 1 for violations)
    """
    print("Checking for test tampering...")
    
    checker = TamperChecker()
    success, violations = checker.check()
    
    if success:
        print("All test/config changes properly marked")
        return 0
    else:
        print("\n❌ Test tampering violations:")
        for violation in violations:
            print(f"  {violation}")
        print("\n💡 To fix: Add '#TEST_CHANGE' to commit message or diff with rationale")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 