#!/usr/bin/env python3
"""Test file to demonstrate diff coverage failure."""

def uncovered_function():
    """This function will not be covered by tests."""
    return "This line should fail diff coverage check"


def covered_function():
    """This function will be covered by tests."""
    return "This line should pass diff coverage check"


if __name__ == "__main__":
    print(covered_function()) 