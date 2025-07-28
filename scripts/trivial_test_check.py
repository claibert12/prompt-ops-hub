#!/usr/bin/env python3
"""Detect trivial tests with zero assertions or trivial asserts."""

import sys
from integrity_core import TrivialTestChecker


def main():
    """Main function."""
    print("Checking for trivial tests...")
    
    checker = TrivialTestChecker()
    success, violations = checker.check()
    
    if success:
        print("No trivial tests found")
        return 0
    else:
        print("Found trivial tests:")
        for violation in violations:
            print(f"  {violation}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 