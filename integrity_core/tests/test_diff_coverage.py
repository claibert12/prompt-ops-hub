"""
Unit tests for DiffCoverageChecker.
"""

import pytest
from unittest.mock import patch, mock_open
from pathlib import Path
from integrity_core.diff_coverage import DiffCoverageChecker
from integrity_core.config import IntegrityConfig


class TestDiffCoverageChecker:
    """Test DiffCoverageChecker functionality."""
    
    def test_init_with_config(self):
        """Test initialization with config."""
        config = IntegrityConfig(min_diff_coverage=95.0)
        checker = DiffCoverageChecker(config)
        assert checker.config.min_diff_coverage == 95.0
    
    def test_init_without_config(self):
        """Test initialization without config."""
        checker = DiffCoverageChecker()
        assert checker.config.min_diff_coverage == 100.0
    
    @patch('subprocess.run')
    def test_get_diff_files_merge_base_success(self, mock_run):
        """Test getting diff files with merge base success."""
        mock_run.side_effect = [
            type('Mock', (), {'returncode': 0, 'stdout': 'abc123\n'})(),
            type('Mock', (), {'returncode': 0, 'stdout': 'src/test.py\nsrc/other.py\n'})(),
        ]
        
        checker = DiffCoverageChecker()
        diff_files = checker.get_diff_files()
        
        assert diff_files == {'src/test.py', 'src/other.py'}
    
    @patch('subprocess.run')
    def test_get_diff_files_fallback_to_origin_main(self, mock_run):
        """Test getting diff files with fallback to origin/main."""
        mock_run.side_effect = [
            type('Mock', (), {'returncode': 1, 'stdout': ''})(),
            type('Mock', (), {'returncode': 0, 'stdout': 'src/test.py\n'})(),
        ]
        
        checker = DiffCoverageChecker()
        diff_files = checker.get_diff_files()
        
        assert diff_files == {'src/test.py'}
    
    @patch('subprocess.run')
    def test_get_diff_files_fallback_to_staged(self, mock_run):
        """Test getting diff files with fallback to staged."""
        mock_run.side_effect = [
            type('Mock', (), {'returncode': 1, 'stdout': ''})(),
            type('Mock', (), {'returncode': 1, 'stdout': ''})(),
            type('Mock', (), {'returncode': 0, 'stdout': 'src/test.py\n'})(),
        ]
        
        checker = DiffCoverageChecker()
        diff_files = checker.get_diff_files()
        
        assert diff_files == {'src/test.py'}
    
    @patch('pathlib.Path.exists')
    def test_parse_coverage_xml_success(self, mock_exists):
        """Test parsing coverage.xml successfully."""
        mock_exists.return_value = True
        
        xml_content = '''<?xml version="1.0" ?>
<coverage version="6.0" timestamp="1234567890" lines-valid="10" lines-covered="8" line-rate="0.8" branches-covered="0" branches-valid="0" branch-rate="0.0" complexity="0.0">
  <sources>
    <source>src</source>
  </sources>
  <packages>
    <package name="test" line-rate="0.8" branch-rate="0.0" complexity="0.0">
      <classes>
        <class name="test.py" filename="src/test.py" line-rate="0.8" branch-rate="0.0" complexity="0.0">
          <lines>
            <line number="1" hits="1"/>
            <line number="2" hits="1"/>
            <line number="3" hits="0"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>'''
        
        with patch('builtins.open', mock_open(read_data=xml_content)):
            checker = DiffCoverageChecker()
            coverage_data = checker.parse_coverage_xml()
            
            assert 'src/test.py' in coverage_data
            assert coverage_data['src/test.py'] == {1, 2}
    
    @patch('pathlib.Path.exists')
    def test_parse_coverage_xml_file_not_found(self, mock_exists):
        """Test parsing coverage.xml when file doesn't exist."""
        mock_exists.return_value = False
        
        checker = DiffCoverageChecker()
        
        with pytest.raises(FileNotFoundError):
            checker.parse_coverage_xml()
    
    @patch('subprocess.run')
    def test_get_changed_lines_success(self, mock_run):
        """Test getting changed lines successfully."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = '''@@ -1,3 +1,4 @@
 line1
+line2
 line3
-line4
+line5'''
        
        checker = DiffCoverageChecker()
        changed_lines = checker.get_changed_lines('src/test.py')
        
        assert changed_lines == {2, 4}
    
    def test_check_diff_coverage_all_covered(self):
        """Test diff coverage check with all lines covered."""
        checker = DiffCoverageChecker()
        
        diff_files = {'src/test.py'}
        coverage_data = {'src/test.py': {1, 2, 3}}
        
        # Mock get_changed_lines to return lines 1 and 2
        with patch.object(checker, 'get_changed_lines', return_value={1, 2}):
            is_covered, uncovered_lines = checker.check_diff_coverage(diff_files, coverage_data)
            
            assert is_covered
            assert len(uncovered_lines) == 0
    
    def test_check_diff_coverage_some_uncovered(self):
        """Test diff coverage check with some lines uncovered."""
        checker = DiffCoverageChecker()
        
        diff_files = {'src/test.py'}
        coverage_data = {'src/test.py': {1, 3}}
        
        # Mock get_changed_lines to return lines 1, 2, and 3
        with patch.object(checker, 'get_changed_lines', return_value={1, 2, 3}):
            is_covered, uncovered_lines = checker.check_diff_coverage(diff_files, coverage_data)
            
            assert not is_covered
            assert len(uncovered_lines) == 1
            assert 'src/test.py:2' in uncovered_lines[0]
    
    def test_check_diff_coverage_renamed_file(self):
        """Test diff coverage check with renamed file."""
        checker = DiffCoverageChecker()
        
        diff_files = {'src/new_name.py'}
        coverage_data = {'src/old_name.py': {1, 2, 3}}
        
        # Mock get_changed_lines to return lines 1 and 2
        with patch.object(checker, 'get_changed_lines', return_value={1, 2}):
            is_covered, uncovered_lines = checker.check_diff_coverage(diff_files, coverage_data)
            
            assert is_covered
            assert len(uncovered_lines) == 0
    
    @patch.object(DiffCoverageChecker, 'get_diff_files')
    @patch.object(DiffCoverageChecker, 'parse_coverage_xml')
    def test_check_no_diff_files(self, mock_parse, mock_get_diff):
        """Test check with no diff files."""
        mock_get_diff.return_value = set()
        
        checker = DiffCoverageChecker()
        success, violations = checker.check()
        
        assert success
        assert len(violations) == 0
    
    @patch.object(DiffCoverageChecker, 'get_diff_files')
    @patch.object(DiffCoverageChecker, 'parse_coverage_xml')
    def test_check_coverage_file_not_found(self, mock_parse, mock_get_diff):
        """Test check with coverage file not found."""
        mock_get_diff.return_value = {'src/test.py'}
        mock_parse.side_effect = FileNotFoundError("coverage.xml not found")
        
        checker = DiffCoverageChecker()
        success, violations = checker.check()
        
        assert not success
        assert len(violations) == 1
        assert "coverage.xml not found" in violations[0]
    
    @patch.object(DiffCoverageChecker, 'get_diff_files')
    @patch.object(DiffCoverageChecker, 'parse_coverage_xml')
    @patch.object(DiffCoverageChecker, 'check_diff_coverage')
    def test_check_success(self, mock_check_diff, mock_parse, mock_get_diff):
        """Test successful check."""
        mock_get_diff.return_value = {'src/test.py'}
        mock_parse.return_value = {'src/test.py': {1, 2, 3}}
        mock_check_diff.return_value = (True, [])
        
        checker = DiffCoverageChecker()
        success, violations = checker.check()
        
        assert success
        assert len(violations) == 0 