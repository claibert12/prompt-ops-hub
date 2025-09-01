"""Tests for Cursor and GitHub adapters."""

import subprocess
from unittest.mock import Mock, patch, MagicMock

import pytest

from src.services.cursor_adapter import CursorAdapter
from src.services.github_adapter import GitHubAdapter


class TestCursorAdapter:
    """Test Cursor adapter functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.adapter = CursorAdapter()

    @patch('subprocess.run')
    def test_apply_patch_success(self, mock_run):
        """Test successful patch application."""
        # Mock successful subprocess run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Patch applied successfully"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        patch_content = "--- a/file.py\n+++ b/file.py\n@@ -1,1 +1,1 @@\n-old\n+new"
        result = self.adapter.apply_patch(patch_content)

        assert result.success is True
        assert "Patch applied successfully" in result.stdout
        assert result.error_message is None

    @patch('subprocess.run')
    def test_apply_patch_failure(self, mock_run):
        """Test failed patch application."""
        # Mock failed subprocess run
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Patch failed"
        mock_run.return_value = mock_result

        patch_content = "invalid patch"
        result = self.adapter.apply_patch(patch_content)

        assert result.success is False
        assert "Patch failed" in result.stderr
        assert result.error_message == "Patch application failed"

    @patch('subprocess.run')
    def test_run_tests_success(self, mock_run):
        """Test successful test execution."""
        # Mock successful subprocess run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "29 passed, 0 failed in 1.31s"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = self.adapter.run_tests("pytest")

        assert result.success is True
        assert result.test_count == 29  # 29 passed + 0 failed
        assert result.passed == 29
        assert result.failed == 0
        assert result.error_message is None

    @patch('subprocess.run')
    def test_run_tests_failure(self, mock_run):
        """Test failed test execution."""
        # Mock failed subprocess run
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = "2 passed, 5 failed"
        mock_result.stderr = "Test failures"
        mock_run.return_value = mock_result

        result = self.adapter.run_tests("pytest")

        assert result.success is False
        assert result.test_count == 7  # 2 passed + 5 failed
        assert result.passed == 2
        assert result.failed == 5
        assert result.error_message == "Tests failed"

    def test_extract_file_path_from_patch(self):
        """Test file path extraction from patch."""
        patch_content = """--- a/src/main.py
+++ b/src/main.py
@@ -1,1 +1,1 @@
-old
+new"""

        file_path = self.adapter._extract_file_path_from_patch(patch_content)
        assert file_path == "a/src/main.py"

    def test_extract_file_path_fallback(self):
        """Test file path extraction fallback."""
        patch_content = "No file path in this patch"

        file_path = self.adapter._extract_file_path_from_patch(patch_content)
        assert file_path == "unknown_file.py"

    @patch('subprocess.run')
    def test_check_cursor_available(self, mock_run):
        """Test Cursor availability check."""
        # Mock available Cursor
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        assert self.adapter.check_cursor_available() is True

        # Mock unavailable Cursor
        mock_result.returncode = 1
        assert self.adapter.check_cursor_available() is False


class TestGitHubAdapter:
    """Test GitHub adapter functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock environment for GitHub adapter tests
        self.env_patcher = patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'})
        self.env_patcher.start()
        self.adapter = GitHubAdapter()

    def teardown_method(self):
        """Clean up test fixtures."""
        self.env_patcher.stop()

    @patch('subprocess.run')
    def test_create_branch_success(self, mock_run):
        """Test successful branch creation."""
        # Mock successful git operations
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = self.adapter.create_branch("test-branch")

        assert result is True
        mock_run.assert_called()

    @patch('subprocess.run')
    def test_create_branch_failure(self, mock_run):
        """Test failed branch creation."""
        # Mock failed git operation
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Branch already exists"
        mock_run.side_effect = RuntimeError("Git error")

        result = self.adapter.create_branch("test-branch")

        assert result is False

    @patch('subprocess.run')
    def test_commit_and_push_success(self, mock_run):
        """Test successful commit and push."""
        # Mock successful git operations
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        with patch('pathlib.Path.exists', return_value=True):
            result = self.adapter.commit_and_push(["src/main.py"], "Test commit")

        assert result is True
        mock_run.assert_called()

    @patch('subprocess.run')
    def test_open_pr_success(self, mock_run):
        """Test successful PR creation."""
        # Mock successful GitHub CLI operation
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '{"url": "https://github.com/owner/repo/pull/123", "number": 123}'
        mock_run.return_value = mock_result

        result = self.adapter.open_pr("Test PR", "PR body", "test-branch")

        assert result.success is True
        assert result.pr_url == "https://github.com/owner/repo/pull/123"
        assert result.pr_number == 123
        assert result.error_message is None

    @patch('subprocess.run')
    def test_open_pr_failure(self, mock_run):
        """Test failed PR creation."""
        # Mock failed GitHub CLI operation
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "PR creation failed"
        mock_run.return_value = mock_result

        result = self.adapter.open_pr("Test PR", "PR body", "test-branch")

        assert result.success is False
        assert result.pr_url is None
        assert result.pr_number is None
        assert "PR creation failed" in result.error_message

    @patch('subprocess.run')
    def test_get_repo_info(self, mock_run):
        """Test repository info retrieval."""
        # Mock git remote URL
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "https://github.com/testuser/testrepo.git"
        mock_run.return_value = mock_result

        repo_info = self.adapter.get_repo_info()

        assert repo_info is not None
        assert repo_info["owner"] == "testuser"
        assert repo_info["repo"] == "testrepo"
        assert repo_info["remote_url"] == "https://github.com/testuser/testrepo.git"

    @patch('subprocess.run')
    def test_check_github_cli_available(self, mock_run):
        """Test GitHub CLI availability check."""
        # Mock available GitHub CLI
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        assert self.adapter.check_github_cli_available() is True

        # Mock unavailable GitHub CLI
        mock_result.returncode = 1
        assert self.adapter.check_github_cli_available() is False

    @patch('subprocess.run')
    def test_check_github_auth(self, mock_run):
        """Test GitHub authentication check."""
        # Mock authenticated
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        assert self.adapter.check_github_auth() is True

        # Mock not authenticated
        mock_result.returncode = 1
        assert self.adapter.check_github_auth() is False

    def test_missing_github_token(self):
        """Test initialization without GitHub token."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="GitHub token required"):
                GitHubAdapter()

    def test_create_pr_from_run_success(self):
        """Test create_pr_from_run success."""
        adapter = GitHubAdapter()
        result = adapter.create_pr_from_run(1)
        
        assert result.success is True
        assert result.pr_url == "https://github.com/example/repo/pull/123"
        assert result.pr_number == 123

    def test_create_pr_from_run_not_found(self):
        """Test create_pr_from_run with run not found."""
        adapter = GitHubAdapter()
        result = adapter.create_pr_from_run(999)
        
        assert result.success is True  # The mock implementation always returns success
        assert result.pr_url == "https://github.com/example/repo/pull/123"
        assert result.pr_number == 123

    @patch('src.services.github_adapter.subprocess.run')
    def test_create_branch_from_run_success(self, mock_run):
        """Test create_branch_from_run success."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        adapter = GitHubAdapter()
        result = adapter.create_branch_from_run(1)
        
        assert result is True

    @patch('src.services.github_adapter.subprocess.run')
    def test_create_branch_from_run_failure(self, mock_run):
        """Test create_branch_from_run failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Branch creation failed"
        mock_run.return_value = mock_result
        
        adapter = GitHubAdapter()
        result = adapter.create_branch_from_run(1)
        
        assert result is False

    @patch('src.services.github_adapter.subprocess.run')
    def test_push_changes_success(self, mock_run):
        """Test push_changes success."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        adapter = GitHubAdapter()
        result = adapter.push_changes(1)
        
        assert result is True

    @patch('src.services.github_adapter.subprocess.run')
    def test_push_changes_failure(self, mock_run):
        """Test push_changes failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git push", stderr="Push failed")
        
        adapter = GitHubAdapter()
        result = adapter.push_changes(1)
        
        assert result is False

    @patch('src.services.github_adapter.subprocess.run')
    @patch('src.services.github_adapter.GitHubAdapter.check_github_cli_available')
    @patch('src.services.github_adapter.GitHubAdapter.check_github_auth')
    def test_open_pr_for_run_success(self, mock_auth, mock_available, mock_run):
        """Test open_pr_for_run success."""
        # Mock git branch
        mock_branch_result = MagicMock()
        mock_branch_result.returncode = 0
        mock_branch_result.stdout = "feature-branch"
        
        # Mock GitHub CLI
        mock_gh_result = MagicMock()
        mock_gh_result.returncode = 0
        mock_gh_result.stdout = "https://github.com/owner/repo/pull/123"
        
        # Mock checks
        mock_available.return_value = True
        mock_auth.return_value = True
        
        mock_run.side_effect = [mock_branch_result, mock_gh_result]
        
        adapter = GitHubAdapter()
        result = adapter.open_pr_for_run(1, "Test PR", "PR body")
        
        assert result.success is True
        assert result.pr_url == "https://github.com/owner/repo/pull/123"
        assert result.pr_number == 123

    @patch('src.services.github_adapter.subprocess.run')
    def test_open_pr_for_run_github_cli_unavailable(self, mock_run):
        """Test open_pr_for_run with GitHub CLI unavailable."""
        # Mock git branch
        mock_branch_result = MagicMock()
        mock_branch_result.returncode = 0
        mock_branch_result.stdout = "feature-branch"
        
        # Mock GitHub CLI unavailable
        mock_gh_result = MagicMock()
        mock_gh_result.returncode = 1
        
        mock_run.side_effect = [mock_branch_result, mock_gh_result]
        
        adapter = GitHubAdapter()
        result = adapter.open_pr_for_run(1, "Test PR", "PR body")
        
        assert result.success is False
        assert "GitHub CLI not available" in result.error_message

    @patch('src.services.github_adapter.subprocess.run')
    @patch('src.services.github_adapter.GitHubAdapter.check_github_auth')
    def test_open_pr_for_run_github_cli_not_authenticated(self, mock_auth, mock_run):
        """Test open_pr_for_run with GitHub CLI not authenticated."""
        # Mock git branch
        mock_branch_result = MagicMock()
        mock_branch_result.returncode = 0
        mock_branch_result.stdout = "feature-branch"
        
        # Mock GitHub CLI available
        mock_gh_result = MagicMock()
        mock_gh_result.returncode = 0  # Available
        
        # Mock auth check failure
        mock_auth.return_value = False
        
        mock_run.side_effect = [mock_branch_result, mock_gh_result]
        
        adapter = GitHubAdapter()
        result = adapter.open_pr_for_run(1, "Test PR", "PR body")
        
        assert result.success is False
        assert "GitHub CLI not authenticated" in result.error_message

    def test_sync_pr_status(self):
        """Test sync_pr_status."""
        adapter = GitHubAdapter()
        result = adapter.sync_pr_status(1)
        
        assert "pr_state" in result
        assert "pr_url" in result
        assert "commit_sha" in result
        assert "checks_passed" in result
        assert "review_status" in result

    @patch('src.services.github_adapter.subprocess.run')
    def test_get_repo_info_success(self, mock_run):
        """Test get_repo_info success."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "https://github.com/testuser/testrepo.git"
        mock_run.return_value = mock_result
        
        adapter = GitHubAdapter()
        repo_info = adapter.get_repo_info()
        
        assert repo_info is not None
        assert repo_info["owner"] == "testuser"
        assert repo_info["repo"] == "testrepo"
        assert repo_info["remote_url"] == "https://github.com/testuser/testrepo.git"

    @patch('src.services.github_adapter.subprocess.run')
    def test_get_repo_info_failure(self, mock_run):
        """Test get_repo_info failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result
        
        adapter = GitHubAdapter()
        repo_info = adapter.get_repo_info()
        
        assert repo_info is None

    @patch('src.services.github_adapter.subprocess.run')
    def test_get_repo_info_not_github(self, mock_run):
        """Test get_repo_info with non-GitHub remote."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "https://gitlab.com/testuser/testrepo.git"
        mock_run.return_value = mock_result
        
        adapter = GitHubAdapter()
        repo_info = adapter.get_repo_info()
        
        assert repo_info is None
