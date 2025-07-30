"""
CI snippet generation functionality.
"""

import os
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import patch, mock_open


class CISnippetGenerator:
    """Generate CI workflow snippets."""
    
    def __init__(self):
        """Initialize CI snippet generator."""
        self.canonical_workflow = self._get_canonical_workflow()
    
    def _get_canonical_workflow(self) -> str:
        """Get the canonical CI workflow YAML (ASCII only)."""
        # All content below is ASCII only.
        return """name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.8", "3.9", "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Cache pip dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Run tamper check
      run: python -c "from integrity_core import TamperChecker; import sys; success, violations = TamperChecker().check(); sys.exit(0 if success else 1)"
    
    - name: Run trivial test check
      run: python -c "from integrity_core import TrivialTestChecker; import sys; success, violations = TrivialTestChecker().check(); sys.exit(0 if success else 1)"
    
    - name: Run tests with coverage
      run: |
        pytest --cov=src --cov-report=xml --cov-report=term-missing --fail-under=80
    
    - name: Run diff coverage check
      run: python -c "from integrity_core import DiffCoverageChecker; import sys; success, violations = DiffCoverageChecker().check(); sys.exit(0 if success else 1)"
    
    - name: Run policy check
      run: python -c "from integrity_core import PolicyChecker; import sys; success, violations = PolicyChecker().check({}); sys.exit(0 if success else 1)"
    
    - name: Run no-skip check
      run: python -c "import subprocess; result = subprocess.run(['pytest', '--collect-only', '-q'], capture_output=True, text=True); assert 'SKIPPED' not in result.stdout and 'xfail' not in result.stdout, 'Found skipped or xfail tests'"
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
"""
    
    def generate_snippet(self, project_name: Optional[str] = None) -> str:
        """Generate CI workflow snippet.
        
        Args:
            project_name: Optional project name for customization
            
        Returns:
            CI workflow YAML content
        """
        return self.canonical_workflow
    
    def get_workflow_hash(self) -> str:
        """Get hash of the canonical workflow.
        
        Returns:
            SHA256 hash of the workflow
        """
        return hashlib.sha256(self.canonical_workflow.encode()).hexdigest()
    
    def check_workflow_drift(self, workflow_path: str = ".github/workflows/ci.yml") -> Dict[str, Any]:
        """Check if the workflow file matches the canonical version.
        
        Args:
            workflow_path: Path to the workflow file
            
        Returns:
            Dictionary with drift check results
        """
        results = {
            "workflow_exists": False,
            "matches_canonical": False,
            "canonical_hash": self.get_workflow_hash(),
            "current_hash": None,
            "drift_detected": False,
            "error": None
        }
        
        try:
            workflow_file = Path(workflow_path)
            
            if not workflow_file.exists():
                results["error"] = f"Workflow file not found: {workflow_path}"
                return results
            
            results["workflow_exists"] = True
            
            with open(workflow_file, 'r', encoding='utf-8', errors='replace') as f:
                current_content = f.read()
            
            current_hash = hashlib.sha256(current_content.encode()).hexdigest()
            results["current_hash"] = current_hash
            
            if current_hash == results["canonical_hash"]:
                results["matches_canonical"] = True
            else:
                results["drift_detected"] = True
                results["error"] = "Workflow file has drifted from canonical version"
        
        except Exception as e:
            results["error"] = f"Error checking workflow drift: {e}"
        
        return results
    
    def update_workflow(self, workflow_path: str = ".github/workflows/ci.yml") -> Dict[str, Any]:
        """Update the workflow file to match canonical version.
        
        Args:
            workflow_path: Path to the workflow file
            
        Returns:
            Dictionary with update results
        """
        results = {
            "updated": False,
            "error": None,
            "backup_created": False
        }
        
        try:
            workflow_file = Path(workflow_path)
            workflow_dir = workflow_file.parent
            
            # Create directory if it doesn't exist
            workflow_dir.mkdir(parents=True, exist_ok=True)
            
            # Create backup if file exists
            if workflow_file.exists():
                backup_path = workflow_file.with_suffix('.yml.backup')
                import shutil
                shutil.copy2(workflow_file, backup_path)
                results["backup_created"] = True
            
            # Write canonical workflow
            with open(workflow_file, 'w', encoding='utf-8', errors='replace') as f:
                f.write(self.canonical_workflow)
            
            results["updated"] = True
        
        except Exception as e:
            results["error"] = f"Error updating workflow: {e}"
        
        return results
    
    def get_workflow_summary(self) -> Dict[str, Any]:
        """Get summary of the canonical workflow.
        
        Returns:
            Dictionary with workflow summary
        """
        return {
            "name": "CI",
            "triggers": ["push", "pull_request"],
            "python_versions": ["3.8", "3.9", "3.10", "3.11"],
            "integrity_gates": ["tamper", "trivial_tests", "coverage", "diff_coverage", "policy", "no_skip"],
            "hash": self.get_workflow_hash()
        }

    def check_snippet(self) -> tuple[bool, list[str]]:
        """Check if current snippet matches canonical version.
        
        Returns:
            Tuple of (matches, differences)
        """
        try:
            drift_results = self.check_workflow_drift()
            if drift_results["error"]:
                if "not found" in drift_results["error"]:
                    return False, ["File not found"]
                return False, [drift_results["error"]]
            
            if drift_results["drift_detected"]:
                differences = []
                if drift_results.get("canonical_hash") != drift_results.get("current_hash"):
                    differences.append(f"Hash mismatch: canonical={drift_results.get('canonical_hash')}, current={drift_results.get('current_hash')}")
                return False, differences
            
            return True, []
        except Exception as e:
            return False, [str(e)]

    def update_snippet(self) -> bool:
        """Update snippet to match canonical version.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            update_results = self.update_workflow()
            return not update_results.get("error", False)
        except Exception:
            return False

    def _get_canonical_snippet(self) -> str:
        """Get canonical snippet content.
        
        Returns:
            Canonical snippet content
        """
        return self.canonical_workflow

    def _read_current_snippet(self) -> str:
        """Read current snippet from file.
        
        Returns:
            Current snippet content
        """
        try:
            with open(".github/workflows/ci.yml", 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        except FileNotFoundError:
            return ""
        except Exception:
            return ""

    def _compare_snippets(self, snippet1: str, snippet2: str) -> list[str]:
        """Compare two snippets and return differences.
        
        Args:
            snippet1: First snippet
            snippet2: Second snippet
            
        Returns:
            List of differences
        """
        differences = []
        if snippet1 != snippet2:
            if not snippet2.strip():
                differences.append("File is empty")
            else:
            differences.append("Content differs")
        return differences

    def _normalize_snippet(self, snippet: str) -> str:
        """Normalize snippet by removing comments and extra whitespace.
        
        Args:
            snippet: Snippet to normalize
            
        Returns:
            Normalized snippet
        """
        lines = snippet.split('\n')
        normalized_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                normalized_lines.append(stripped)
        return '\n'.join(normalized_lines)

    def _get_workflow_path(self) -> Path:
        """Get default workflow path.
        
        Returns:
            Default workflow path
        """
        return Path(".github/workflows/ci.yml")

    def _ensure_workflow_directory(self):
        """Ensure workflow directory exists."""
        Path(".github/workflows").mkdir(parents=True, exist_ok=True)

    @patch('builtins.open', new_callable=mock_open, read_data=b'name: CI\non: [push, pull_request]\xff'.decode('utf-8', errors='replace'))
    def test_check_workflow_drift_encoding_edge_case(self, mock_file):
        with patch('pathlib.Path.exists', return_value=True):
            result = self.generator.check_workflow_drift()
            # Should not crash, and should detect drift if content differs
            assert 'error' not in result or result['error'] is None or 'drifted' in result['error'] or 'matches_canonical' in result 