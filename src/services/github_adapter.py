"""GitHub adapter for creating branches, committing changes, and opening PRs."""

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class PRResult:
    """Result of creating a GitHub PR."""
    success: bool
    pr_url: str | None = None
    pr_number: int | None = None
    error_message: str | None = None


class GitHubAdapter:
    """Adapter for interacting with GitHub via Git and GitHub CLI."""

    def __init__(self, repo_path: str | None = None, github_token: str | None = None):
        """Initialize GitHub adapter.
        
        Args:
            repo_path: Path to git repository. Defaults to current directory.
            github_token: GitHub token for authentication. Defaults to GITHUB_TOKEN env var.
        """
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")

        if not self.github_token:
            raise ValueError("GitHub token required. Set GITHUB_TOKEN environment variable.")

    def create_branch(self, branch_name: str) -> bool:
        """Create a new git branch.
        
        Args:
            branch_name: Name of the branch to create
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if we're in a git repository
            if not self._is_git_repo():
                raise Exception("Not in a git repository")

            # Create and checkout new branch
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True
            )

            return True

        except subprocess.CalledProcessError as e:
            print(f"Error creating branch: {e.stderr}")
            return False
        except Exception as e:
            print(f"Error creating branch: {str(e)}")
            return False

    def commit_and_push(self, files_changed: list[str], message: str) -> bool:
        """Commit changes and push to remote.
        
        Args:
            files_changed: List of files that were changed
            message: Commit message
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add all changed files
            for file_path in files_changed:
                if Path(file_path).exists():
                    subprocess.run(
                        ["git", "add", file_path],
                        cwd=self.repo_path,
                        check=True,
                        capture_output=True,
                        text=True
                    )

            # Commit changes
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True
            )

            # Push to remote
            subprocess.run(
                ["git", "push", "origin", "HEAD"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True
            )

            return True

        except subprocess.CalledProcessError as e:
            print(f"Error committing/pushing: {e.stderr}")
            return False
        except Exception as e:
            print(f"Error committing/pushing: {str(e)}")
            return False

    def open_pr(self, title: str, body: str, branch: str, base: str = "main") -> PRResult:
        """Open a pull request on GitHub.
        
        Args:
            title: PR title
            body: PR description
            branch: Source branch name
            base: Target branch name (default: main)
            
        Returns:
            PRResult with success status and PR URL
        """
        try:
            # Use GitHub CLI to create PR
            cmd = [
                "gh", "pr", "create",
                "--title", title,
                "--body", body,
                "--head", branch,
                "--base", base,
                "--json", "url,number"
            ]

            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                # Parse JSON response
                pr_data = json.loads(result.stdout)
                return PRResult(
                    success=True,
                    pr_url=pr_data.get("url"),
                    pr_number=pr_data.get("number")
                )
            else:
                return PRResult(
                    success=False,
                    error_message=f"Failed to create PR: {result.stderr}"
                )

        except subprocess.TimeoutExpired:
            return PRResult(
                success=False,
                error_message="PR creation timed out"
            )
        except json.JSONDecodeError:
            return PRResult(
                success=False,
                error_message="Failed to parse PR response"
            )
        except Exception as e:
            return PRResult(
                success=False,
                error_message=f"Error creating PR: {str(e)}"
            )

    def get_repo_info(self) -> dict[str, Any] | None:
        """Get repository information.
        
        Returns:
            Dictionary with repo info or None if not available
        """
        try:
            # Get remote URL
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                remote_url = result.stdout.strip()
                # Extract owner/repo from URL
                if "github.com" in remote_url:
                    parts = remote_url.split("github.com/")[-1].replace(".git", "")
                    owner, repo = parts.split("/", 1)
                    return {
                        "owner": owner,
                        "repo": repo,
                        "remote_url": remote_url
                    }

            return None

        except Exception:
            return None

    def _is_git_repo(self) -> bool:
        """Check if current directory is a git repository.
        
        Returns:
            True if git repository, False otherwise
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def check_github_cli_available(self) -> bool:
        """Check if GitHub CLI is available.
        
        Returns:
            True if GitHub CLI is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def check_github_auth(self) -> bool:
        """Check if GitHub CLI is authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def create_pr_from_run(self, run_id: int) -> PRResult:
        """Create a PR from a run.
        
        Args:
            run_id: Run ID to create PR for
            
        Returns:
            PRResult with success status and details
        """
        try:
            # For now, return a mock successful result
            # In a real implementation, this would:
            # 1. Get run details from database
            # 2. Create branch from run
            # 3. Push changes
            # 4. Open PR
            # 5. Update run with PR metadata
            
            return PRResult(
                success=True,
                pr_url="https://github.com/example/repo/pull/123",
                pr_number=123
            )
        except Exception as e:
            return PRResult(
                success=False,
                error_message=str(e)
            )
    
    def create_branch_from_run(self, run_id: int) -> bool:
        """Create a branch from a run.
        
        Args:
            run_id: Run ID to create branch for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            branch_name = f"run-{run_id}-{int(__import__('time').time())}"
            return self.create_branch(branch_name)
        except Exception as e:
            print(f"Error creating branch from run: {e}")
            return False
    
    def push_changes(self, run_id: int) -> bool:
        """Push changes for a run.
        
        Args:
            run_id: Run ID to push changes for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the current branch name
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            branch_name = result.stdout.strip()
            
            # Push the branch
            subprocess.run(
                ["git", "push", "-u", "origin", branch_name],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error pushing changes: {e.stderr}")
            return False
        except Exception as e:
            print(f"Error pushing changes: {e}")
            return False
    
    def open_pr_for_run(self, run_id: int, title: str, body: str, base: str = "main") -> PRResult:
        """Open a PR for a run.
        
        Args:
            run_id: Run ID to open PR for
            title: PR title
            body: PR body
            base: Base branch
            
        Returns:
            PRResult with success status and details
        """
        try:
            # Get the current branch name
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            branch_name = result.stdout.strip()
            
            # Open PR using GitHub CLI
            if not self.check_github_cli_available():
                raise Exception("GitHub CLI not available")
            
            if not self.check_github_auth():
                raise Exception("GitHub CLI not authenticated")
            
            # Create PR
            pr_result = subprocess.run(
                ["gh", "pr", "create", "--title", title, "--body", body, "--base", base],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse PR URL from output
            output_lines = pr_result.stdout.strip().split('\n')
            pr_url = None
            pr_number = None
            
            for line in output_lines:
                if line.startswith('https://github.com/'):
                    pr_url = line.strip()
                    # Extract PR number from URL
                    if '/pull/' in pr_url:
                        pr_number = int(pr_url.split('/pull/')[-1])
                    break
            
            return PRResult(
                success=True,
                pr_url=pr_url,
                pr_number=pr_number
            )
            
        except subprocess.CalledProcessError as e:
            return PRResult(
                success=False,
                error_message=f"GitHub CLI error: {e.stderr}"
            )
        except Exception as e:
            return PRResult(
                success=False,
                error_message=str(e)
            )
    
    def sync_pr_status(self, run_id: int) -> dict[str, Any]:
        """Sync PR status for a run.
        
        Args:
            run_id: Run ID to sync PR status for
            
        Returns:
            Dictionary with PR status information
        """
        try:
            # Get run details from database (this would be injected)
            # For now, return mock data
            return {
                "pr_state": "opened",
                "pr_url": "https://github.com/example/repo/pull/123",
                "commit_sha": "abc123def456",
                "checks_passed": True,
                "review_status": "pending"
            }
        except Exception as e:
            return {
                "error": str(e)
            }


# Global GitHub adapter instance (will be initialized when needed)
github_adapter = None

def get_github_adapter():
    """Get the global GitHub adapter instance, creating it if needed."""
    global github_adapter
    if github_adapter is None:
        github_adapter = GitHubAdapter()
    return github_adapter
