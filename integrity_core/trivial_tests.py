"""
Trivial test detection functionality.
"""

import ast
from pathlib import Path
from typing import List, Tuple, Optional
from .config import IntegrityConfig


class TrivialTestChecker:
    """Detect trivial tests with zero assertions or trivial asserts."""
    
    def __init__(self, config: Optional[IntegrityConfig] = None):
        """Initialize trivial test checker.
        
        Args:
            config: Configuration for trivial test checks
        """
        self.config = config or IntegrityConfig()
    
    def find_test_files(self) -> List[Path]:
        """Find all test files in the project.
        
        Returns:
            List of test file paths
        """
        test_files = []
        tests_dir = Path("tests")
        if tests_dir.exists():
            for test_file in tests_dir.rglob("test_*.py"):
                test_files.append(test_file)
        return test_files
    
    def has_meaningful_assertions(self, node: ast.AST) -> bool:
        """Check if a test function has meaningful assertions.
        
        Args:
            node: AST node to check
            
        Returns:
            True if meaningful assertions found
        """
        assertions = []
        
        for child in ast.walk(node):
            if isinstance(child, ast.Assert):
                # Check if assertion is trivial
                if isinstance(child.test, ast.Constant):
                    # assert True, assert False, assert None
                    if child.test.value in (True, False, None):
                        continue
                elif isinstance(child.test, ast.Name):
                    # assert variable_name (without comparison)
                    continue
                elif isinstance(child.test, ast.Compare):
                    # Check for trivial comparisons
                    if len(child.test.ops) == 1:
                        op = child.test.ops[0]
                        if isinstance(op, ast.Eq):
                            # assert x == True, assert x == False
                            if isinstance(child.test.comparators[0], ast.Constant):
                                if child.test.comparators[0].value in (True, False):
                                    continue
                assertions.append(child)
            elif isinstance(child, ast.Call):
                # Check for pytest.raises, assert_called, etc.
                if isinstance(child.func, ast.Attribute):
                    if child.func.attr in ['raises', 'assert_called', 'assert_called_once', 'assert_called_with', 'readouterr', 'assert_equal', 'assert_true', 'assert_false', 'assert_in', 'assert_not_in', 'assert_is', 'assert_is_not']:
                        assertions.append(child)
                    elif isinstance(child.func.value, ast.Name) and child.func.value.id == 'pytest':
                        if child.func.attr in ['raises', 'mark', 'parametrize', 'fixture']:
                            assertions.append(child)
                    elif isinstance(child.func.value, ast.Attribute) and child.func.value.attr == 'pytest':
                        if child.func.attr in ['raises', 'mark', 'parametrize', 'fixture']:
                            assertions.append(child)
                elif isinstance(child.func, ast.Name):
                    if child.func.id in ['raises', 'pytest_raises']:
                        assertions.append(child)
            elif isinstance(child, ast.With):
                # Check for pytest.raises context manager
                if isinstance(child.items[0].context_expr, ast.Call):
                    if isinstance(child.items[0].context_expr.func, ast.Attribute):
                        if child.items[0].context_expr.func.attr == 'raises':
                            assertions.append(child)
                    elif isinstance(child.items[0].context_expr.func, ast.Name):
                        if child.items[0].context_expr.func.id in ['raises', 'pytest_raises']:
                            assertions.append(child)
            elif isinstance(child, ast.Expr):
                # Check for standalone function calls that might be assertions
                if isinstance(child.value, ast.Call):
                    if isinstance(child.value.func, ast.Attribute):
                        if child.value.func.attr.startswith('assert_'):
                            assertions.append(child)
        
        return len(assertions) > 0
    
    def has_pytest_decorators(self, node: ast.FunctionDef) -> bool:
        """Check if function has pytest decorators that make it non-trivial.
        
        Args:
            node: Function definition node
            
        Returns:
            True if pytest decorators found
        """
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Attribute):
                    if decorator.func.attr in ['parametrize', 'mark', 'fixture']:
                        return True
                elif isinstance(decorator.func, ast.Name):
                    if decorator.func.id in ['parametrize', 'mark', 'fixture']:
                        return True
            elif isinstance(decorator, ast.Attribute):
                if decorator.attr in ['parametrize', 'mark', 'fixture']:
                    return True
        return False
    
    def analyze_test_file(self, file_path: Path) -> List[Tuple[str, str]]:
        """Analyze a test file for trivial tests.
        - Do not flag tests using pytest.raises
        - Do not flag tests with asserts in helper functions (detect via AST)
        - Support #ALLOW_TRIVIAL marker above the function
        Args:
            file_path: Path to test file
        Returns:
            List of (test_name, reason) tuples for trivial tests
        """
        trivial_tests = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content)
            lines = content.splitlines()
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    # Check for #ALLOW_TRIVIAL marker above the function
                    func_lineno = node.lineno - 1
                    allow_trivial = False
                    for i in range(max(0, func_lineno-2), func_lineno):
                        if '#ALLOW_TRIVIAL' in lines[i]:
                            allow_trivial = True
                            break
                    if allow_trivial:
                        continue
                    # Skip if pytest decorators are present
                    if self.has_pytest_decorators(node):
                        continue
                    # Check for pytest.raises in the function
                    has_pytest_raises = False
                    for child in ast.walk(node):
                        if isinstance(child, ast.With):
                            if hasattr(child, 'items') and child.items:
                                context_expr = child.items[0].context_expr
                                if isinstance(context_expr, ast.Call):
                                    if hasattr(context_expr.func, 'attr') and context_expr.func.attr == 'raises':
                                        has_pytest_raises = True
                        if isinstance(child, ast.Call):
                            if hasattr(child.func, 'attr') and child.func.attr == 'raises':
                                has_pytest_raises = True
                    if has_pytest_raises:
                        continue
                    # Check for assert in helper functions called by this test
                    # (simple: if any call in the function body is to a function defined in the same file that contains assert)
                    helper_assert_found = False
                    for child in ast.walk(node):
                        if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                            helper_name = child.func.id
                            for n in ast.walk(tree):
                                if isinstance(n, ast.FunctionDef) and n.name == helper_name:
                                    if any(isinstance(grandchild, ast.Assert) for grandchild in ast.walk(n)):
                                        helper_assert_found = True
                    if helper_assert_found:
                        continue
                    if not self.has_meaningful_assertions(node):
                        trivial_tests.append((node.name, "No meaningful assertions"))
        except (SyntaxError, UnicodeDecodeError) as e:
            trivial_tests.append(("parse_error", f"Could not parse file: {e}"))
        return trivial_tests
    
    def check(self) -> Tuple[bool, List[str]]:
        """Run trivial test check.
        
        Returns:
            Tuple of (success, violations)
        """
        violations = []
        
        if self.config.allow_trivial_tests:
            return True, violations
        
        test_files = self.find_test_files()
        if not test_files:
            return True, violations
        
        all_trivial_tests = []
        
        for test_file in test_files:
            trivial_tests = self.analyze_test_file(test_file)
            if trivial_tests:
                for test_name, reason in trivial_tests:
                    all_trivial_tests.append((str(test_file), test_name, reason))
        
        if all_trivial_tests:
            violations.append("Found trivial tests:")
            for file_path, test_name, reason in all_trivial_tests:
                violations.append(f"  - {file_path}::{test_name}: {reason}")
        
        return len(violations) == 0, violations 