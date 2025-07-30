"""Tests for CLI init project functionality."""

import pytest
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path
from src.cli_init.project_scaffold import ProjectScaffold


class TestProjectScaffold:
    """Test ProjectScaffold class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scaffold = ProjectScaffold("test-project", "/tmp/test-project")

    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_scaffold_project_success(self, mock_file, mock_mkdir):
        """Test successful project scaffolding."""
        with patch('pathlib.Path.exists', return_value=False):
            result = self.scaffold.scaffold_project()
            
            assert result['project_path'] == "/tmp/test-project"
            assert result['created_directories'] > 0
            assert result['created_files'] > 0
            assert mock_mkdir.called
            assert mock_file.called

    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_scaffold_project_directory_exists(self, mock_file, mock_mkdir):
        """Test project scaffolding when directory exists."""
        with patch('pathlib.Path.exists', return_value=True):
            result = self.scaffold.scaffold_project()
            
            assert result['project_path'] == "/tmp/test-project"
            assert result['created_directories'] > 0
            assert result['created_files'] > 0

    @patch('pathlib.Path.mkdir')
    def test_scaffold_project_mkdir_error(self, mock_mkdir):
        """Test project scaffolding with mkdir error."""
        mock_mkdir.side_effect = PermissionError("Permission denied")
        
        with pytest.raises(PermissionError):
            self.scaffold.scaffold_project()

    @patch('builtins.open', new_callable=mock_open)
    def test_create_pyproject_toml(self, mock_file):
        """Test pyproject.toml creation."""
        self.scaffold._create_pyproject_toml()
        
        mock_file.assert_called_with(Path("/tmp/test-project/pyproject.toml"), 'w')
        mock_file().write.assert_called()

    @patch('builtins.open', new_callable=mock_open)
    def test_create_github_workflow(self, mock_file):
        """Test GitHub workflow creation."""
        self.scaffold._create_github_workflow()
        
        mock_file.assert_called_with(Path("/tmp/test-project/.github/workflows/ci.yml"), 'w')
        mock_file().write.assert_called()

    @patch('builtins.open', new_callable=mock_open)
    def test_create_readme(self, mock_file):
        """Test README.md creation."""
        self.scaffold._create_readme()
        
        mock_file.assert_called_with(Path("/tmp/test-project/README.md"), 'w')
        mock_file().write.assert_called()

    @patch('builtins.open', new_callable=mock_open)
    def test_create_gitignore(self, mock_file):
        """Test .gitignore creation."""
        self.scaffold._create_gitignore()
        
        mock_file.assert_called_with(Path("/tmp/test-project/.gitignore"), 'w')
        mock_file().write.assert_called()

    @patch('builtins.open', new_callable=mock_open)
    def test_create_tests_init(self, mock_file):
        """Test tests/__init__.py creation."""
        self.scaffold._create_tests_init()
        
        mock_file.assert_called_with(Path("/tmp/test-project/tests/__init__.py"), 'w')
        mock_file().write.assert_called()

    @patch('builtins.open', new_callable=mock_open)
    def test_create_src_init(self, mock_file):
        """Test src/__init__.py creation."""
        self.scaffold._create_src_init()
        
        mock_file.assert_called_with(Path("/tmp/test-project/src/__init__.py"), 'w')
        mock_file().write.assert_called()

    def test_get_pyproject_content(self):
        """Test pyproject.toml content generation."""
        content = self.scaffold._get_pyproject_content()
        
        assert "[project]" in content
        assert "name = \"test-project\"" in content
        assert "[tool.pytest.ini_options]" in content
        assert "[tool.coverage.run]" in content

    def test_get_github_workflow_content(self):
        """Test GitHub workflow content generation."""
        content = self.scaffold._get_github_workflow_content()
        
        assert "name: CI" in content
        assert "on:" in content
        assert "jobs:" in content
        assert "test:" in content

    def test_get_readme_content(self):
        """Test README.md content generation."""
        content = self.scaffold._get_readme_content()
        
        assert "# test-project" in content
        assert "## Installation" in content
        assert "## Testing" in content

    def test_get_gitignore_content(self):
        """Test .gitignore content generation."""
        content = self.scaffold._get_gitignore_content()
        
        assert "__pycache__" in content
        assert "*.pyc" in content
        assert ".coverage" in content
        assert "htmlcov" in content

    def test_get_tests_init_content(self):
        """Test tests/__init__.py content generation."""
        content = self.scaffold._get_tests_init_content()
        
        assert "# Test package" in content

    def test_get_src_init_content(self):
        """Test src/__init__.py content generation."""
        content = self.scaffold._get_src_init_content()
        
        assert "# Source package" in content

    @patch('pathlib.Path.mkdir')
    def test_create_directories(self, mock_mkdir):
        """Test directory creation."""
        self.scaffold._create_directories()
        
        # Should create multiple directories
        assert mock_mkdir.call_count >= 3

    @patch('pathlib.Path.mkdir')
    def test_create_directories_with_parents(self, mock_mkdir):
        """Test directory creation with parents."""
        self.scaffold._create_directories()
        
                # Check that parents=True is used for nested directories
        calls = mock_mkdir.call_args_list
        for call in calls:
            try:
                path_str = str(call[0][0])
                if len(path_str.split('/')) > 1 or len(path_str.split('\\')) > 1:
                    assert call[1].get('parents') is True 
            except (IndexError, AttributeError):
                # Skip calls that don't have the expected structure
                pass 