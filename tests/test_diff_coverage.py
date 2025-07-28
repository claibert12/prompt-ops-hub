"""Test for diff coverage demonstration."""

from test_diff_coverage import covered_function


def test_covered_function():
    """Test the covered function."""
    result = covered_function()
    assert result == "This line should pass diff coverage check"


# Note: uncovered_function() is intentionally not tested to demonstrate diff coverage failure 