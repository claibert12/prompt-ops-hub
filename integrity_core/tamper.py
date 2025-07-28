"""
Test tampering detection functionality.
"""

import re
import subprocess
from pathlib import Path
from typing import List, Set, Optional
from .config import IntegrityConfig


class TamperChecker:
    """Detect test tampering without proper markers."""
    
    def __init__(self, config: Optional[IntegrityConfig] = None):
        """Initialize tamper checker.
        
        Args:
            config: Configuration for tamper checks
        """
        self.config = config or IntegrityConfig()
    
    def get_staged_files(self) -> Set[str]:
        """Get list of staged files in git.
        
        Returns:
            Set of staged file paths
        """
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                check=True
            )
            return set(result.stdout.strip().split('\n')) if result.stdout.strip() else set()
        except subprocess.CalledProcessError:
            return set()
    
    def get_pr_files(self) -> Set[str]:
        """Get list of files changed in current PR.
        
        Returns:
            Set of changed file paths
        """
        try:
            # Try to get PR diff against origin/main
            result = subprocess.run(
                ["git", "diff", "origin/main", "--name-only"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0 and result.stdout.strip():
                return set(result.stdout.strip().split('\n'))
            
            # Fallback to staged files
            return self.get_staged_files()
        except Exception:
            return self.get_staged_files()
    
    def get_deleted_files(self) -> Set[str]:
        """Get list of files deleted in current PR.
        
        Returns:
            Set of deleted file paths
        """
        try:
            # Get deleted files from diff against origin/main
            result = subprocess.run(
                ["git", "diff", "origin/main", "--name-status"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0 and result.stdout.strip():
                deleted_files = set()
                for line in result.stdout.strip().split('\n'):
                    if line.startswith('D\t'):
                        file_path = line[2:]  # Remove 'D\t' prefix
                        deleted_files.add(file_path)
                return deleted_files
            
            return set()
        except Exception:
            return set()
    
    def is_test_or_config_file(self, file_path: str) -> bool:
        """Check if file is a test or config file that requires #TEST_CHANGE marker.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file requires marker
        """
        # Skip whitelisted files
        for whitelist_pattern in self.config.tamper_whitelist:
            if whitelist_pattern in file_path:
                return False
        
        test_patterns = [
            r'^tests/',
            r'\.github/workflows/',
            r'pyproject\.toml$',
            r'\.coveragerc$',
            r'pytest\.ini$',
            r'tox\.ini$',
            r'\.pre-commit-config\.yaml$'
        ]
        
        return any(re.match(pattern, file_path) for pattern in test_patterns)
    
    def check_test_change_marker(self, file_path: str) -> bool:
        """Check if file has #TEST_CHANGE marker in commit message or diff.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if marker is present
        """
        try:
            # Check commit message
            result = subprocess.run(
                ["git", "log", "-1", "--pretty=format:%B"],
                capture_output=True,
                text=True,
                check=True
            )
            if "#TEST_CHANGE" in result.stdout:
                return True
            
            # Check staged diff for this file
            result = subprocess.run(
                ["git", "diff", "--cached", file_path],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0 and "#TEST_CHANGE" in result.stdout:
                return True
            
            # Check PR diff for this file
            result = subprocess.run(
                ["git", "diff", "origin/main", file_path],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0 and "#TEST_CHANGE" in result.stdout:
                return True
            
            return False
        
        except Exception:
            return False
    
    def check(self) -> tuple[bool, List[str]]:
        """Run tamper check.
        
        Returns:
            Tuple of (success, violations)
        """
        violations = []
        
        if not self.config.tamper_check_enabled:
            return True, violations
        
        # Get changed and deleted files
        changed_files = self.get_pr_files()
        deleted_files = self.get_deleted_files()
        
        if not changed_files and not deleted_files:
            return True, violations
        
        # Check for test/config files
        test_config_files = [
            f for f in changed_files 
            if f and self.is_test_or_config_file(f)
        ]
        
        # Check for deleted test files
        deleted_test_files = [
            f for f in deleted_files 
            if f and self.is_test_or_config_file(f)
        ]
        
        if not test_config_files and not deleted_test_files:
            return True, violations
        
        # Check for #TEST_CHANGE markers
        # Check changed files
        for file_path in test_config_files:
            if not self.check_test_change_marker(file_path):
                violations.append(
                    f"Missing #TEST_CHANGE marker: {file_path} "
                    f"(test/config changes require marker + rationale)"
                )
        
        # Check deleted files
        for file_path in deleted_test_files:
            if not self.check_test_change_marker(file_path):
                violations.append(
                    f"Missing #TEST_CHANGE marker: {file_path} "
                    f"(test/config deletions require marker + rationale)"
                )
        
        return len(violations) == 0, violations 