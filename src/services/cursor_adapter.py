"""Cursor IDE adapter for applying patches and running tests."""

import os
import subprocess
import tempfile
from dataclasses import dataclass


@dataclass
class ApplyResult:
    """Result of applying a patch via Cursor."""
    success: bool
    stdout: str
    stderr: str
    error_message: str | None = None


@dataclass
class TestResult:
    """Result of running tests via Cursor."""
    success: bool
    stdout: str
    stderr: str
    test_count: int = 0
    passed: int = 0
    failed: int = 0
    error_message: str | None = None


class CursorAdapter:
    """Adapter for interacting with Cursor IDE."""

    def __init__(self, cursor_cli_path: str | None = None):
        """Initialize Cursor adapter.
        
        Args:
            cursor_cli_path: Path to Cursor CLI. Defaults to 'cursor' in PATH.
        """
        self.cursor_cli_path = cursor_cli_path or "cursor"

    def apply_patch(self, patch: str, file_path: str | None = None) -> ApplyResult:
        """Apply a patch via Cursor CLI.
        
        Args:
            patch: Unified diff patch content
            file_path: Target file path (optional, will be extracted from patch)
            
        Returns:
            ApplyResult with success status and output
        """
        try:
            # Create temporary patch file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
                f.write(patch)
                patch_file = f.name

            try:
                # Extract file path from patch if not provided
                if not file_path:
                    file_path = self._extract_file_path_from_patch(patch)

                # Apply patch using Cursor CLI
                cmd = [
                    self.cursor_cli_path,
                    "apply-patch",
                    "--patch-file", patch_file,
                    "--target-file", file_path
                ]

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                return ApplyResult(
                    success=result.returncode == 0,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    error_message=None if result.returncode == 0 else "Patch application failed"
                )

            finally:
                # Clean up temporary patch file
                os.unlink(patch_file)

        except subprocess.TimeoutExpired:
            return ApplyResult(
                success=False,
                stdout="",
                stderr="",
                error_message="Patch application timed out"
            )
        except Exception as e:
            return ApplyResult(
                success=False,
                stdout="",
                stderr="",
                error_message=f"Error applying patch: {str(e)}"
            )

    def run_tests(self, test_command: str = "pytest") -> TestResult:
        """Run tests via Cursor CLI.
        
        Args:
            test_command: Test command to run (default: pytest)
            
        Returns:
            TestResult with test execution results
        """
        try:
            # Run tests using Cursor CLI
            cmd = [
                self.cursor_cli_path,
                "run-command",
                "--command", test_command
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            # Parse test results (basic parsing for now)
            test_count, passed, failed = self._parse_test_output(result.stdout)

            return TestResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                test_count=test_count,
                passed=passed,
                failed=failed,
                error_message=None if result.returncode == 0 else "Tests failed"
            )

        except subprocess.TimeoutExpired:
            return TestResult(
                success=False,
                stdout="",
                stderr="",
                error_message="Test execution timed out"
            )
        except Exception as e:
            return TestResult(
                success=False,
                stdout="",
                stderr="",
                error_message=f"Error running tests: {str(e)}"
            )

    def _extract_file_path_from_patch(self, patch: str) -> str:
        """Extract target file path from patch content.
        
        Args:
            patch: Unified diff patch content
            
        Returns:
            Target file path
        """
        lines = patch.split('\n')
        for line in lines:
            if line.startswith('--- ') or line.startswith('+++ '):
                # Extract file path from diff header
                parts = line.split()
                if len(parts) >= 2:
                    return parts[1]

        # Default fallback
        return "unknown_file.py"

    def _parse_test_output(self, output: str) -> tuple[int, int, int]:
        """Parse pytest output to extract test counts.
        
        Args:
            output: Test command output
            
        Returns:
            Tuple of (total, passed, failed) test counts
        """
        try:
            # Look for pytest summary line
            lines = output.split('\n')
            for line in lines:
                if 'passed' in line and 'failed' in line:
                    # Extract numbers from line like "29 passed, 1 warning in 1.31s"
                    import re
                    numbers = re.findall(r'(\d+)', line)
                    if len(numbers) >= 2:
                        passed = int(numbers[0])
                        failed = int(numbers[1]) if len(numbers) > 1 else 0
                        return passed + failed, passed, failed

            # Fallback: count lines with test results
            passed = len([line for line in lines if 'PASSED' in line])
            failed = len([line for line in lines if 'FAILED' in line])
            return passed + failed, passed, failed

        except Exception:
            return 0, 0, 0

    def check_cursor_available(self) -> bool:
        """Check if Cursor CLI is available.
        
        Returns:
            True if Cursor CLI is available, False otherwise
        """
        try:
            result = subprocess.run(
                [self.cursor_cli_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False


# Global Cursor adapter instance
cursor_adapter = CursorAdapter()
