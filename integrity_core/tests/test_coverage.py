"""
Unit tests for CoverageChecker.
"""

import pytest
from unittest.mock import patch, mock_open
from pathlib import Path
from integrity_core.coverage import CoverageChecker
from integrity_core.config import IntegrityConfig


class TestCoverageChecker:
    """Test CoverageChecker functionality."""
    
    def test_init_with_config(self):
        """Test initialization with config."""
        config = IntegrityConfig(min_coverage=85.0)
        checker = CoverageChecker(config)
        assert checker.config.min_coverage == 85.0
    
    def test_init_without_config(self):
        """Test initialization without config."""
        checker = CoverageChecker()
        assert checker.config.min_coverage == 80.0
    
    def test_find_coverage_thresholds_pyproject(self):
        """Test finding coverage thresholds in pyproject.toml."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.read_text', return_value='fail_under = 85'):
            checker = CoverageChecker()
            thresholds = checker.find_coverage_thresholds()
            
            assert len(thresholds) >= 1
            pyproject_found = any(t[0] == "pyproject.toml" and t[1] == 85 for t in thresholds)
            assert pyproject_found
    
    def test_find_coverage_thresholds_coveragerc(self):
        """Test finding coverage thresholds in .coveragerc."""
        with patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.read_text', return_value='fail_under = 90'):
            checker = CoverageChecker()
            thresholds = checker.find_coverage_thresholds()
            
            assert len(thresholds) >= 1
            coveragerc_found = any(t[0] == ".coveragerc" and t[1] == 90 for t in thresholds)
            assert coveragerc_found
    
    @patch('subprocess.run')
    def test_get_baseline_threshold_success(self, mock_run):
        """Test getting baseline threshold successfully."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = 'fail_under = 85'
        
        checker = CoverageChecker()
        baseline = checker.get_baseline_threshold()
        
        assert baseline == 85
    
    @patch('subprocess.run')
    def test_get_baseline_threshold_fallback(self, mock_run):
        """Test getting baseline threshold with fallback."""
        mock_run.return_value.returncode = 1
        
        checker = CoverageChecker()
        baseline = checker.get_baseline_threshold()
        
        assert baseline == 80
    
    def test_check_threshold_values_valid(self):
        """Test checking valid threshold values."""
        checker = CoverageChecker()
        thresholds = [("pyproject.toml", 85), (".coveragerc", 90)]
        
        violations = checker.check_threshold_values(thresholds)
        
        assert len(violations) == 0
    
    def test_check_threshold_values_invalid(self):
        """Test checking invalid threshold values."""
        checker = CoverageChecker()
        thresholds = [("pyproject.toml", 75), (".coveragerc", 90)]
        
        violations = checker.check_threshold_values(thresholds)
        
        assert len(violations) == 1
        assert "Coverage threshold too low" in violations[0]
    
    @patch('subprocess.run')
    def test_check_threshold_changes_no_changes(self, mock_run):
        """Test checking threshold changes with no changes."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        
        checker = CoverageChecker()
        violations = checker.check_threshold_changes()
        
        assert len(violations) == 0
    
    @patch('subprocess.run')
    def test_check_threshold_changes_with_decrease(self, mock_run):
        """Test checking threshold changes with decrease."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "- fail_under = 85\n+ fail_under = 75"
        
        checker = CoverageChecker()
        violations = checker.check_threshold_changes()
        
        assert len(violations) == 1
        assert "Coverage threshold lowered" in violations[0]
    
    @patch('pathlib.Path.exists')
    def test_check_no_thresholds(self, mock_exists):
        """Test check with no thresholds found."""
        mock_exists.return_value = False
        
        checker = CoverageChecker()
        success, violations = checker.check()
        
        assert not success
        assert len(violations) == 1
        assert "No coverage thresholds found" in violations[0]
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='fail_under = 85')
    def test_check_success(self, mock_file, mock_exists):
        """Test successful check."""
        mock_exists.return_value = True
        
        with patch('pathlib.Path.read_text', return_value='fail_under = 85'):
            checker = CoverageChecker()
            success, violations = checker.check()
            
            assert success
            assert len(violations) == 0 