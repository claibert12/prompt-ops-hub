"""Tests for observer module."""

import pytest
from unittest.mock import patch, MagicMock

from src.observer.observer import Observer
from src.observer.models import IntegrityReport, IntegrityViolation, ViolationType


class TestObserver:
    """Test observer functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.observer = Observer()

    def test_build_integrity_report_good_run(self):
        """Test integrity report for a good run."""
        run_data = {
            'coverage': 85,
            'baseline_coverage': 80,
            'diff_coverage': 100,
            'skipped_tests': 0,
            'deleted_test_files': [],
            'threshold_changed': False,
            'code_lines': 1000,
            'test_lines': 200,
            'content': 'Clean code with no weasel words',
            'claimed_success': True,
            'pytest_success': True
        }
        
        report = self.observer.build_integrity_report("test-run-1", run_data)
        
        assert report.run_id == "test-run-1"
        assert report.score == 100.0
        assert len(report.violations) == 0
        assert len(report.questions) == 0
        assert "Excellent integrity" in report.summary

    def test_build_integrity_report_coverage_drop(self):
        """Test integrity report for coverage drop."""
        run_data = {
            'coverage': 70,  # Dropped from 80
            'baseline_coverage': 80,
            'diff_coverage': 100,
            'skipped_tests': 0,
            'deleted_test_files': [],
            'threshold_changed': False,
            'code_lines': 1000,
            'test_lines': 200,
            'content': 'Clean code',
            'claimed_success': True,
            'pytest_success': True
        }
        
        report = self.observer.build_integrity_report("test-run-2", run_data)
        
        assert report.score < 100.0
        assert len(report.violations) == 1
        assert report.violations[0].type == ViolationType.COVERAGE_DROP
        assert len(report.questions) == 1
        assert "coverage drop" in report.questions[0].lower()

    def test_build_integrity_report_weasel_words(self):
        """Test integrity report for weasel words."""
        run_data = {
            'coverage': 85,
            'baseline_coverage': 80,
            'diff_coverage': 100,
            'skipped_tests': 0,
            'deleted_test_files': [],
            'threshold_changed': False,
            'code_lines': 1000,
            'test_lines': 200,
            'content': 'This is a temporary fix just to pass the tests',
            'claimed_success': True,
            'pytest_success': True
        }
        
        report = self.observer.build_integrity_report("test-run-3", run_data)
        
        assert report.score < 100.0
        assert len(report.violations) == 1
        assert report.violations[0].type == ViolationType.WEASEL_WORDS
        assert "weasel words" in report.violations[0].message
        assert len(report.questions) == 1

    def test_build_integrity_report_claim_mismatch(self):
        """Test integrity report for claim mismatch."""
        run_data = {
            'coverage': 85,
            'baseline_coverage': 80,
            'diff_coverage': 100,
            'skipped_tests': 0,
            'deleted_test_files': [],
            'threshold_changed': False,
            'code_lines': 1000,
            'test_lines': 200,
            'content': 'Clean code',
            'claimed_success': True,
            'pytest_success': False  # Mismatch
        }
        
        report = self.observer.build_integrity_report("test-run-4", run_data)
        
        assert report.score < 100.0
        assert len(report.violations) == 1
        assert report.violations[0].type == ViolationType.CLAIM_MISMATCH
        assert len(report.questions) == 1

    def test_build_integrity_report_multiple_violations(self):
        """Test integrity report for multiple violations."""
        run_data = {
            'coverage': 70,
            'baseline_coverage': 80,
            'diff_coverage': 85,
            'skipped_tests': 5,
            'deleted_test_files': ['test_file.py'],
            'threshold_changed': True,
            'code_lines': 1000,
            'test_lines': 50,  # Low ratio
            'content': 'Temporary fix TODO later',
            'claimed_success': True,
            'pytest_success': False
        }
        
        report = self.observer.build_integrity_report("test-run-5", run_data)
        
        assert report.score < 50.0  # Should be very low
        assert len(report.violations) >= 5
        assert len(report.questions) >= 5

    def test_calculate_score_no_violations(self):
        """Test score calculation with no violations."""
        violations = []
        score = self.observer._calculate_score(violations)
        assert score == 100.0

    def test_calculate_score_with_violations(self):
        """Test score calculation with violations."""
        violations = [
            IntegrityViolation(
                type=ViolationType.COVERAGE_DROP,
                message="Coverage dropped",
                severity="critical",
                weight=2.0
            )
        ]
        score = self.observer._calculate_score(violations)
        assert score < 100.0

    def test_get_severity_multiplier(self):
        """Test severity multiplier calculation."""
        assert self.observer._get_severity_multiplier("warning") == 5
        assert self.observer._get_severity_multiplier("error") == 10
        assert self.observer._get_severity_multiplier("critical") == 20
        assert self.observer._get_severity_multiplier("unknown") == 10

    def test_generate_summary(self):
        """Test summary generation."""
        violations = []
        
        summary = self.observer._generate_summary(95, violations)
        assert "Excellent" in summary
        
        summary = self.observer._generate_summary(85, violations)
        assert "Good" in summary
        
        summary = self.observer._generate_summary(75, violations)
        assert "Acceptable" in summary
        
        summary = self.observer._generate_summary(65, violations)
        assert "Poor" in summary 