"""Tests for CI self-verification script."""

import pytest
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import xml.etree.ElementTree as ET

from scripts.ci_self_check import CISelfCheck


class TestCISelfCheck:
    """Test CI self-verification functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.checker = CISelfCheck()
    
    def test_init(self):
        """Test CISelfCheck initialization."""
        assert self.checker.repo_root == Path.cwd()
        assert self.checker.results == []
    
    def test_run_check_success(self):
        """Test successful check execution."""
        def mock_check():
            return True, "Success"
        
        success, details = self.checker.run_check("test_check", mock_check)
        
        assert success is True
        assert details == "Success"
        assert len(self.checker.results) == 1
        assert self.checker.results[0]['name'] == "test_check"
        assert self.checker.results[0]['success'] is True
    
    def test_run_check_failure(self):
        """Test failed check execution."""
        def mock_check():
            return False, "Failure"
        
        success, details = self.checker.run_check("test_check", mock_check)
        
        assert success is False
        assert details == "Failure"
        assert len(self.checker.results) == 1
        assert self.checker.results[0]['name'] == "test_check"
        assert self.checker.results[0]['success'] is False
    
    def test_run_check_exception(self):
        """Test check execution with exception."""
        def mock_check():
            raise ValueError("Test exception")
        
        success, details = self.checker.run_check("test_check", mock_check)
        
        assert success is False
        assert "Test exception" in details
        assert len(self.checker.results) == 1
        assert self.checker.results[0]['name'] == "test_check"
        assert self.checker.results[0]['success'] is False
    
    @patch('subprocess.run')
    def test_check_pytest_success(self, mock_run):
        """Test successful pytest check."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test passed"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        success, details = self.checker.check_pytest()
        
        assert success is True
        assert "All tests passed" in details
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_check_pytest_failure(self, mock_run):
        """Test failed pytest check."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "test failed"
        mock_result.stderr = "error"
        mock_run.return_value = mock_result
        
        success, details = self.checker.check_pytest()
        
        assert success is False
        assert "pytest failed with exit code 1" in details
    
    @patch('subprocess.run')
    def test_check_pytest_skipped_tests(self, mock_run):
        """Test pytest check with skipped tests."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "1 skipped"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        success, details = self.checker.check_pytest()
        
        assert success is False
        assert "skipped or xfail tests" in details
    
    @patch('pathlib.Path.exists')
    @patch('xml.etree.ElementTree.parse')
    def test_check_coverage_threshold_success(self, mock_parse, mock_exists):
        """Test successful coverage threshold check."""
        mock_exists.return_value = True
        
        mock_root = MagicMock()
        mock_root.attrib = {'line-rate': '0.85'}
        mock_tree = MagicMock()
        mock_tree.getroot.return_value = mock_root
        mock_parse.return_value = mock_tree
        
        success, details = self.checker.check_coverage_threshold()
        
        assert success is True
        assert "85.0% >= 80% threshold" in details
    
    @patch('pathlib.Path.exists')
    def test_check_coverage_threshold_file_missing(self, mock_exists):
        """Test coverage threshold check with missing file."""
        mock_exists.return_value = False
        
        success, details = self.checker.check_coverage_threshold()
        
        assert success is False
        assert "coverage.xml not found" in details
    
    @patch('pathlib.Path.exists')
    @patch('xml.etree.ElementTree.parse')
    def test_check_coverage_threshold_below_threshold(self, mock_parse, mock_exists):
        """Test coverage threshold check below threshold."""
        mock_exists.return_value = True
        
        mock_root = MagicMock()
        mock_root.attrib = {'line-rate': '0.75'}
        mock_tree = MagicMock()
        mock_tree.getroot.return_value = mock_root
        mock_parse.return_value = mock_tree
        
        success, details = self.checker.check_coverage_threshold()
        
        assert success is False
        assert "75.0% < 80% threshold" in details
    
    @patch('subprocess.run')
    def test_check_diff_coverage_success(self, mock_run):
        """Test successful diff coverage check."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Diff coverage = 100%"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        success, details = self.checker.check_diff_coverage()
        
        assert success is True
        assert "Diff coverage = 100%" in details
    
    @patch('subprocess.run')
    def test_check_diff_coverage_failure(self, mock_run):
        """Test failed diff coverage check."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "Diff coverage failed"
        mock_result.stderr = "error"
        mock_run.return_value = mock_result
        
        success, details = self.checker.check_diff_coverage()
        
        assert success is False
        assert "Diff coverage check failed" in details
    
    @patch('subprocess.run')
    def test_check_thresholds_success(self, mock_run):
        """Test successful thresholds check."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Thresholds maintained"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        success, details = self.checker.check_thresholds()
        
        assert success is True
        assert "Coverage thresholds maintained" in details
    
    @patch('subprocess.run')
    def test_check_test_tamper_success(self, mock_run):
        """Test successful test tamper check."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "No tampering detected"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        success, details = self.checker.check_test_tamper()
        
        assert success is True
        assert "No test tampering detected" in details
    
    @patch('subprocess.run')
    def test_check_trivial_tests_success(self, mock_run):
        """Test successful trivial tests check."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "No trivial tests"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        success, details = self.checker.check_trivial_tests()
        
        assert success is True
        assert "No trivial tests detected" in details
    
    @patch('subprocess.run')
    def test_check_ci_snippet_success(self, mock_run):
        """Test successful CI snippet check."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "CI workflow matches"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        success, details = self.checker.check_ci_snippet()
        
        assert success is True
        assert "CI workflow matches canonical version" in details
    
    @patch('sys.path')
    @patch('src.core.policy.policy_engine')
    @patch('src.core.guardrails.guardrails')
    def test_check_policy_success(self, mock_guardrails, mock_policy_engine, mock_path):
        """Test successful policy check."""
        mock_result = MagicMock()
        mock_result.allowed = True
        mock_result.violations = []
        mock_policy_engine.evaluate_policy.return_value = mock_result
        
        mock_guardrails.check_policy_results.return_value = []
        
        success, details = self.checker.check_policy()
        
        assert success is True
        assert "Policy check passed" in details
    
    @patch('sys.path')
    @patch('src.core.policy.policy_engine')
    @patch('src.core.guardrails.guardrails')
    def test_check_policy_failure(self, mock_guardrails, mock_policy_engine, mock_path):
        """Test failed policy check."""
        mock_result = MagicMock()
        mock_result.allowed = False
        mock_result.violations = ["violation1"]
        mock_policy_engine.evaluate_policy.return_value = mock_result
        
        mock_guardrails.check_policy_results.return_value = ["violation1"]
        
        success, details = self.checker.check_policy()
        
        assert success is False
        assert "Policy check failed" in details
    
    @patch('sys.path')
    @patch('integrity_core.observer.Observer')
    def test_check_observer_success(self, mock_observer_class, mock_path):
        """Test successful observer check."""
        mock_observer = MagicMock()
        mock_observer.calculate_integrity_score.return_value = 85
        mock_observer_class.return_value = mock_observer
        
        success, details = self.checker.check_observer()
        
        assert success is True
        assert "85 >= 70" in details
    
    @patch('sys.path')
    @patch('integrity_core.observer.Observer')
    def test_check_observer_failure(self, mock_observer_class, mock_path):
        """Test failed observer check."""
        mock_observer = MagicMock()
        mock_observer.calculate_integrity_score.return_value = 65
        mock_observer_class.return_value = mock_observer
        
        success, details = self.checker.check_observer()
        
        assert success is False
        assert "65 < 70 threshold" in details
    
    @patch('builtins.print')
    def test_print_summary_all_passed(self, mock_print):
        """Test summary printing with all checks passed."""
        self.checker.results = [
            {'name': 'test1', 'success': True, 'details': 'Success'},
            {'name': 'test2', 'success': True, 'details': 'Success'},
        ]
        
        result = self.checker.print_summary()
        
        assert result is True
        mock_print.assert_called()
    
    @patch('builtins.print')
    def test_print_summary_some_failed(self, mock_print):
        """Test summary printing with some checks failed."""
        self.checker.results = [
            {'name': 'test1', 'success': True, 'details': 'Success'},
            {'name': 'test2', 'success': False, 'details': 'Failure'},
        ]
        
        result = self.checker.print_summary()
        
        assert result is False
        mock_print.assert_called()
    
    @patch.object(CISelfCheck, 'run_check')
    @patch.object(CISelfCheck, 'print_summary')
    def test_run_all_checks(self, mock_print_summary, mock_run_check):
        """Test running all checks."""
        mock_print_summary.return_value = True
        mock_run_check.return_value = (True, "Success")
        
        result = self.checker.run_all_checks()
        
        assert result is True
        assert mock_run_check.call_count == 9  # Number of checks
        mock_print_summary.assert_called_once()


class TestCISelfCheckIntegration:
    """Integration tests for CI self-check script."""
    
    def test_script_execution(self):
        """Test that the script can be executed."""
        script_path = Path("scripts/ci_self_check.py")
        assert script_path.exists(), "CI self-check script should exist"
        
        # Test that the script can be imported
        try:
            import scripts.ci_self_check
            assert hasattr(scripts.ci_self_check, 'CISelfCheck')
        except ImportError as e:
            pytest.fail(f"Failed to import CI self-check script: {e}")
    
    def test_script_has_main_function(self):
        """Test that the script has a main function."""
        script_path = Path("scripts/ci_self_check.py")
        with open(script_path, encoding='utf-8') as f:
            content = f.read()
            assert "def main():" in content
            assert "if __name__ == \"__main__\":" in content
    
    def test_script_exit_codes(self):
        """Test that the script exits with correct codes."""
        # This would require running the actual script, which might fail
        # in a test environment, so we'll just verify the structure
        script_path = Path("scripts/ci_self_check.py")
        with open(script_path, encoding='utf-8') as f:
            content = f.read()
            assert "sys.exit(1)" in content  # Should exit 1 on failure
            assert "sys.exit(0)" not in content  # Should not explicitly exit 0 on success


# Test data for coverage XML
SAMPLE_COVERAGE_XML = '''<?xml version="1.0" ?>
<coverage line-rate="0.85" branch-rate="0.75" lines-covered="100" lines-valid="120" branches-covered="30" branches-valid="40" complexity="0.0" version="6.3.2" timestamp="1234567890">
    <sources>
        <source>src</source>
    </sources>
    <packages>
        <package name="src" line-rate="0.85" branch-rate="0.75" complexity="0.0">
            <classes>
                <class name="test_module" filename="src/test_module.py" line-rate="0.85" branch-rate="0.75" complexity="0.0">
                    <methods/>
                    <lines>
                        <line number="1" hits="1"/>
                        <line number="2" hits="1"/>
                    </lines>
                </class>
            </classes>
        </package>
    </packages>
</coverage>'''


class TestCISelfCheckCoverageParsing:
    """Test coverage XML parsing functionality."""
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data=SAMPLE_COVERAGE_XML)
    def test_parse_coverage_xml(self, mock_file, mock_exists):
        """Test parsing coverage XML file."""
        mock_exists.return_value = True
        
        checker = CISelfCheck()
        success, details = checker.check_coverage_threshold()
        
        # Should pass since coverage is 85% >= 80%
        assert success is True
        assert "85.0% >= 80% threshold" in details
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data=SAMPLE_COVERAGE_XML.replace('0.85', '0.75'))
    def test_parse_coverage_xml_below_threshold(self, mock_file, mock_exists):
        """Test parsing coverage XML file below threshold."""
        mock_exists.return_value = True
        
        checker = CISelfCheck()
        success, details = checker.check_coverage_threshold()
        
        # Should fail since coverage is 75% < 80%
        assert success is False
        assert "75.0% < 80% threshold" in details 