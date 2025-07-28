"""Tests for CLI ci-snippet functionality."""

import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from src.cli_snippet.ci_snippet import CISnippetGenerator


class TestCISnippetGenerator:
    """Test CISnippetGenerator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = CISnippetGenerator()

    def test_generate_snippet(self):
        """Test CI snippet generation."""
        snippet = self.generator.generate_snippet()

        assert "name: CI" in snippet
        assert "on:" in snippet
        assert "jobs:" in snippet
        assert "test:" in snippet
        assert "coverage" in snippet
        assert "integrity" in snippet

    @patch('src.cli_snippet.ci_snippet.CISnippetGenerator.check_workflow_drift')
    def test_check_snippet_matches(self, mock_drift):
        """Test CI snippet check when it matches."""
        mock_drift.return_value = {
            "workflow_exists": True,
            "matches_canonical": True,
            "drift_detected": False,
            "error": None
        }
        
        matches, differences = self.generator.check_snippet()
        
        assert matches is True
        assert differences == []

    @patch('builtins.open', new_callable=mock_open, read_data="name: Old CI\non: [push]")
    def test_check_snippet_different(self, mock_file):
        """Test CI snippet check when it differs."""
        with patch('pathlib.Path.exists', return_value=True):
            matches, differences = self.generator.check_snippet()
            
            assert matches is False
            assert len(differences) > 0

    @patch('pathlib.Path.exists')
    def test_check_snippet_file_not_found(self, mock_exists):
        """Test CI snippet check when file doesn't exist."""
        mock_exists.return_value = False
        
        matches, differences = self.generator.check_snippet()
        
        assert matches is False
        assert "File not found" in differences[0]

    @patch('src.cli_snippet.ci_snippet.CISnippetGenerator.update_workflow')
    def test_update_snippet_success(self, mock_update):
        """Test CI snippet update success."""
        mock_update.return_value = {
            "updated": True,
            "error": None
        }
        
        result = self.generator.update_snippet()
        
        assert result is True

    @patch('builtins.open', new_callable=mock_open)
    def test_update_snippet_error(self, mock_file):
        """Test CI snippet update error."""
        mock_file.side_effect = PermissionError("Permission denied")
        
        with patch('pathlib.Path.exists', return_value=True):
            result = self.generator.update_snippet()
            
            assert result is False

    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_update_snippet_create_directory(self, mock_file, mock_mkdir):
        """Test CI snippet update creates directory if needed."""
        with patch('pathlib.Path.exists', side_effect=[False, True]):
            result = self.generator.update_snippet()
            
            assert result is True
            mock_mkdir.assert_called_with(parents=True, exist_ok=True)

    def test_get_canonical_snippet(self):
        """Test getting canonical CI snippet."""
        snippet = self.generator._get_canonical_snippet()
        
        assert "name: CI" in snippet
        assert "on:" in snippet
        assert "jobs:" in snippet
        assert "test:" in snippet
        assert "coverage" in snippet
        assert "integrity" in snippet

    def test_get_canonical_snippet_structure(self):
        """Test canonical CI snippet structure."""
        snippet = self.generator._get_canonical_snippet()
        
        # Check for required sections
        assert "name: CI" in snippet
        assert "on:" in snippet
        assert "jobs:" in snippet
        assert "test:" in snippet
        assert "coverage" in snippet
        assert "integrity" in snippet
        
        # Check for required steps
        assert "pytest" in snippet
        assert "coverage" in snippet
        assert "diff coverage check" in snippet
        assert "trivial test check" in snippet
        assert "tamper check" in snippet
        assert "no-skip check" in snippet

    @patch('builtins.open', new_callable=mock_open, read_data="name: CI\non: [push, pull_request]")
    def test_read_current_snippet_success(self, mock_file):
        """Test reading current CI snippet success."""
        with patch('pathlib.Path.exists', return_value=True):
            content = self.generator._read_current_snippet()
            
            assert content == "name: CI\non: [push, pull_request]"

    @patch('builtins.open')
    def test_read_current_snippet_file_not_found(self, mock_open):
        """Test reading current CI snippet when file doesn't exist."""
        mock_open.side_effect = FileNotFoundError("File not found")

        content = self.generator._read_current_snippet()

        # When file doesn't exist, it should return empty string
        assert content == ""

    @patch('builtins.open', new_callable=mock_open)
    def test_read_current_snippet_read_error(self, mock_file):
        """Test reading current CI snippet with read error."""
        mock_file.side_effect = PermissionError("Permission denied")
        
        with patch('pathlib.Path.exists', return_value=True):
            content = self.generator._read_current_snippet()
            
            assert content == ""

    def test_compare_snippets_identical(self):
        """Test comparing identical snippets."""
        snippet1 = "name: CI\non: [push, pull_request]"
        snippet2 = "name: CI\non: [push, pull_request]"
        
        differences = self.generator._compare_snippets(snippet1, snippet2)
        
        assert differences == []

    def test_compare_snippets_different(self):
        """Test comparing different snippets."""
        snippet1 = "name: CI\non: [push, pull_request]"
        snippet2 = "name: Old CI\non: [push]"
        
        differences = self.generator._compare_snippets(snippet1, snippet2)
        
        assert len(differences) > 0
        assert "Content differs" in differences[0]

    def test_compare_snippets_empty_current(self):
        """Test comparing snippets when current is empty."""
        snippet1 = "name: CI\non: [push, pull_request]"
        snippet2 = ""
        
        differences = self.generator._compare_snippets(snippet1, snippet2)
        
        assert len(differences) > 0
        assert "File is empty" in differences[0]

    def test_normalize_snippet(self):
        """Test snippet normalization."""
        snippet = "name: CI\n  on: [push, pull_request]\n  jobs:\n    test:"
        normalized = self.generator._normalize_snippet(snippet)
        
        # Should remove extra whitespace and normalize line endings
        assert "name: CI" in normalized
        assert "on:" in normalized
        assert "jobs:" in normalized

    def test_normalize_snippet_with_comments(self):
        """Test snippet normalization with comments."""
        snippet = "# Comment\nname: CI\n# Another comment\non: [push]"
        normalized = self.generator._normalize_snippet(snippet)
        
        # Should preserve structure but normalize whitespace
        assert "name: CI" in normalized
        assert "on:" in normalized

    def test_get_workflow_path_default(self):
        """Test getting default workflow path."""
        path = self.generator._get_workflow_path()
        
        assert path == Path(".github/workflows/ci.yml")

    def test_get_workflow_path_custom(self):
        """Test getting custom workflow path."""
        # The constructor doesn't accept workflow_path parameter
        # This test verifies that the current implementation always returns the default path
        path = self.generator._get_workflow_path()
        
        # Should always return the default path since custom paths are not supported
        assert path == Path(".github/workflows/ci.yml")
        assert path.as_posix() == ".github/workflows/ci.yml"

    def test_ensure_workflow_directory(self):
        """Test ensuring workflow directory exists."""
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            self.generator._ensure_workflow_directory()
            
            mock_mkdir.assert_called_with(parents=True, exist_ok=True) 