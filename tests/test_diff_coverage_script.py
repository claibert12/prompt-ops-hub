"""Test diff coverage script functionality."""

import pytest
from unittest.mock import patch, mock_open
from integrity_core import DiffCoverageChecker


class TestDiffCoverageScript:
    """Test diff coverage script functionality."""
    
    def test_parse_coverage_xml_success(self):
        """Test parsing coverage.xml successfully."""
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
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=xml_content)):
                checker = DiffCoverageChecker()
                coverage_data = checker.parse_coverage_xml()
                
                assert 'src/test.py' in coverage_data
                assert coverage_data['src/test.py'] == {1, 2}
    
    def test_parse_coverage_xml_file_not_found(self):
        """Test parsing coverage.xml when file doesn't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            checker = DiffCoverageChecker()
            
            with pytest.raises(FileNotFoundError):
                checker.parse_coverage_xml()
    
    @patch('subprocess.run')
    def test_get_diff_files_success(self, mock_run):
        """Test getting diff files successfully."""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = 'src/test.py\nsrc/other.py\n'
        
        checker = DiffCoverageChecker()
        diff_files = checker.get_diff_files()
        
        assert diff_files == {'src/test.py', 'src/other.py'}
    
    def test_check_diff_coverage_all_covered(self):
        """Test diff coverage check with all lines covered."""
        checker = DiffCoverageChecker()
        diff_files = {'src/test.py'}
        coverage_data = {'src/test.py': {1, 2, 3}}
        # Mock get_changed_lines to return lines 1 and 2
        with patch.object(checker, 'get_changed_lines', return_value={1, 2}):
            is_covered, uncovered_lines = checker.check_diff_coverage(diff_files, coverage_data)
            assert is_covered is True
            assert uncovered_lines == []
    
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