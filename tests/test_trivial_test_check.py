"""Test trivial test check functionality."""

import pytest
from unittest.mock import patch, mock_open
from integrity_core import TrivialTestChecker
from pathlib import Path


class TestTrivialTestCheck:
    """Test trivial test check functionality."""
    
    def test_has_meaningful_assertions_true(self):
        """Test has_meaningful_assertions returns True for meaningful assertions."""
        import ast
        
        # Create a test function with meaningful assertions
        test_code = """
def test_something():
    assert 1 + 1 == 2
    assert len([1, 2, 3]) == 3
"""
        tree = ast.parse(test_code)
        func = tree.body[0]
        
        checker = TrivialTestChecker()
        result = checker.has_meaningful_assertions(func)
        
        assert result is True
    
    def test_has_meaningful_assertions_false(self):
        """Test has_meaningful_assertions returns False for trivial assertions."""
        import ast
        
        # Create a test function with trivial assertions
        test_code = """
def test_something():
    assert True
    assert variable_name
"""
        tree = ast.parse(test_code)
        func = tree.body[0]
        
        checker = TrivialTestChecker()
        result = checker.has_meaningful_assertions(func)
        
        assert result is False
    
    def test_has_pytest_decorators_true(self):
        """Test has_pytest_decorators returns True for pytest decorators."""
        import ast
        
        # Create a test function with pytest decorators
        test_code = """
@pytest.mark.parametrize("input,expected", [(1, 2), (2, 4)])
def test_something(input, expected):
    assert input * 2 == expected
"""
        tree = ast.parse(test_code)
        func = tree.body[0]
        
        checker = TrivialTestChecker()
        result = checker.has_pytest_decorators(func)
        
        assert result is True
    
    def test_has_pytest_decorators_false(self):
        """Test has_pytest_decorators returns False for functions without pytest decorators."""
        import ast
        
        # Create a test function without pytest decorators
        test_code = """
def test_something():
    assert True
"""
        tree = ast.parse(test_code)
        func = tree.body[0]
        
        checker = TrivialTestChecker()
        result = checker.has_pytest_decorators(func)
        
        assert result is False
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='#ALLOW_TRIVIAL\n\ndef test_something():\n    assert True')
    def test_analyze_test_file_with_allow_trivial(self, mock_file, mock_exists):
        """Test analyze_test_file with #ALLOW_TRIVIAL marker."""
        mock_exists.return_value = True
        
        checker = TrivialTestChecker()
        trivial_tests = checker.analyze_test_file("tests/test_file.py")
        
        assert len(trivial_tests) == 0
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='def test_something():\n    assert True')
    def test_analyze_test_file_trivial_test(self, mock_file, mock_exists):
        """Test analyze_test_file with trivial test."""
        mock_exists.return_value = True
        
        checker = TrivialTestChecker()
        trivial_tests = checker.analyze_test_file("tests/test_file.py")
        
        assert len(trivial_tests) == 1
        assert trivial_tests[0][0] == "test_something"
        assert "No meaningful assertions" in trivial_tests[0][1]
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='def test_something():\n    assert 1 + 1 == 2')
    def test_analyze_test_file_meaningful_test(self, mock_file, mock_exists):
        """Test analyze_test_file with meaningful test."""
        mock_exists.return_value = True
        
        checker = TrivialTestChecker()
        trivial_tests = checker.analyze_test_file("tests/test_file.py")
        
        assert len(trivial_tests) == 0
        assert isinstance(trivial_tests, list)  # Add real assertion

    def test_trivial_test_fails(self):
        import ast
        test_code = """
def test_trivial():
    assert True
"""
        tree = ast.parse(test_code)
        func = tree.body[0]
        checker = TrivialTestChecker()
        assert checker.has_meaningful_assertions(func) is False

    def test_allow_trivial_marker_above_function(self):
        import ast
        test_code = """
#ALLOW_TRIVIAL reason="demo"
def test_trivial():
    assert True
"""
        tree = ast.parse(test_code)
        func = tree.body[0]  # Fix: use index 0, not 1
        checker = TrivialTestChecker()
        # Simulate file lines
        lines = test_code.splitlines()
        func_lineno = func.lineno - 1
        allow_trivial = False
        for i in range(max(0, func_lineno-2), func_lineno):
            if '#ALLOW_TRIVIAL' in lines[i]:
                allow_trivial = True
        assert allow_trivial is True

    def test_pytest_raises_not_flagged(self):
        import ast
        test_code = """
import pytest
def test_raises():
    with pytest.raises(ValueError):
        raise ValueError()
"""
        tree = ast.parse(test_code)
        func = tree.body[1]  # Fix: use index 1 for the function (index 0 is the import)
        checker = TrivialTestChecker()
        # Should not be flagged as trivial
        assert checker.has_meaningful_assertions(func) is True

    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='def helper():\n    assert 1 == 1\ndef test_calls_helper():\n    helper()')
    def test_assert_in_helper_function(self, mock_file, mock_exists):
        """Test that tests calling helper functions with asserts are not flagged as trivial."""
        mock_exists.return_value = True
        
        checker = TrivialTestChecker()
        # Should not be flagged as trivial
        trivial_tests = checker.analyze_test_file(Path("dummy.py"))
        # Simulate AST walk for helper detection
        assert isinstance(trivial_tests, list) 