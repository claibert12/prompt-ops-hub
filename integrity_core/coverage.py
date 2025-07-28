"""
Coverage checking functionality.
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from .config import IntegrityConfig


class CoverageChecker:
    """Check coverage thresholds and prevent lowering."""
    
    def __init__(self, config: Optional[IntegrityConfig] = None):
        """Initialize coverage checker.
        
        Args:
            config: Configuration for coverage checks
        """
        self.config = config or IntegrityConfig()
    
    def find_coverage_thresholds(self) -> List[Tuple[str, int]]:
        """Find all coverage fail-under thresholds in the repo.
        
        Returns:
            List of (file_path, threshold_value) tuples
        """
        thresholds = []
        
        # Check pyproject.toml
        pyproject_path = Path("pyproject.toml")
        if pyproject_path.exists():
            try:
                content = pyproject_path.read_text(encoding='utf-8')
                match = re.search(r'fail_under\s*=\s*(\d+)', content)
                if match:
                    thresholds.append((str(pyproject_path), int(match.group(1))))
            except UnicodeDecodeError:
                pass
        
        # Check .coveragerc
        coveragerc_path = Path(".coveragerc")
        if coveragerc_path.exists():
            try:
                content = coveragerc_path.read_text(encoding='utf-8')
                match = re.search(r'fail_under\s*=\s*(\d+)', content)
                if match:
                    thresholds.append((str(coveragerc_path), int(match.group(1))))
            except UnicodeDecodeError:
                pass
        
        # Check CI files
        ci_dir = Path(".github/workflows")
        if ci_dir.exists():
            for yaml_file in ci_dir.glob("*.yml"):
                try:
                    content = yaml_file.read_text(encoding='utf-8')
                    match = re.search(r'--fail-under=(\d+)', content)
                    if match:
                        thresholds.append((str(yaml_file), int(match.group(1))))
                except UnicodeDecodeError:
                    continue
        
        return thresholds
    
    def get_baseline_threshold(self) -> int:
        """Get baseline threshold from origin/main or default to 80.
        
        Returns:
            Baseline threshold value
        """
        try:
            # Try to get threshold from origin/main
            result = subprocess.run(
                ["git", "show", "origin/main:pyproject.toml"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                match = re.search(r'fail_under\s*=\s*(\d+)', result.stdout)
                if match:
                    return int(match.group(1))
        except Exception:
            pass
        
        # Default baseline
        return 80
    
    def check_threshold_values(self, thresholds: List[Tuple[str, int]]) -> List[str]:
        """Check if any thresholds are below baseline or minimum.
        
        Args:
            thresholds: List of (file_path, threshold_value) tuples
            
        Returns:
            List of violation messages
        """
        violations = []
        baseline = self.get_baseline_threshold()
        min_threshold = max(baseline, int(self.config.min_coverage))
        
        for file_path, threshold in thresholds:
            if threshold < min_threshold:
                violations.append(
                    f"Coverage threshold too low: {file_path} = {threshold}% "
                    f"(minimum {min_threshold}%, baseline {baseline}%)"
                )
        
        return violations
    
    def check_threshold_changes(self) -> List[str]:
        """Check if coverage thresholds were lowered in this PR.
        
        Returns:
            List of violation messages
        """
        violations = []
        
        try:
            # Get diff for coverage-related files
            result = subprocess.run(
                ["git", "diff", "HEAD~1", "--", "pyproject.toml", ".coveragerc", ".github/workflows/"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0 and result.stdout:
                # Look for threshold decreases
                lines = result.stdout.split('\n')
                for i, line in enumerate(lines):
                    if 'fail_under' in line and '-' in line:
                        # Check if next line shows a decrease
                        if i + 1 < len(lines) and '+' in lines[i + 1]:
                            old_match = re.search(r'fail_under\s*=\s*(\d+)', line)
                            new_match = re.search(r'fail_under\s*=\s*(\d+)', lines[i + 1])
                            
                            if old_match and new_match:
                                old_val = int(old_match.group(1))
                                new_val = int(new_match.group(1))
                                
                                if new_val < old_val:
                                    violations.append(
                                        f"Coverage threshold lowered: {old_val}% → {new_val}% "
                                        f"(violates integrity rules)"
                                    )
        
        except Exception as e:
            violations.append(f"Error checking threshold changes: {e}")
        
        return violations
    
    def check(self) -> Tuple[bool, List[str]]:
        """Run all coverage checks.
        
        Returns:
            Tuple of (success, violations)
        """
        violations = []
        
        # Find all thresholds
        thresholds = self.find_coverage_thresholds()
        
        if not thresholds:
            violations.append("No coverage thresholds found")
            return False, violations
        
        # Check threshold values
        value_violations = self.check_threshold_values(thresholds)
        violations.extend(value_violations)
        
        # Check for threshold changes
        change_violations = self.check_threshold_changes()
        violations.extend(change_violations)
        
        return len(violations) == 0, violations 