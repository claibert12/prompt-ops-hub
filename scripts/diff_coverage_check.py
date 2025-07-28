#!/usr/bin/env python3
"""Check diff coverage against coverage.xml and fail if below 100%."""

import sys
from integrity_core import DiffCoverageChecker


def main():
    """Main function."""
    print("Checking diff coverage...")
    
    checker = DiffCoverageChecker()
    success, violations = checker.check()
    
    if success:
        print("100% diff coverage achieved!")
        return 0
    else:
        print("❌ Diff coverage below 100%")
        print("Violations:")
        for violation in violations:
            print(f"  - {violation}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 