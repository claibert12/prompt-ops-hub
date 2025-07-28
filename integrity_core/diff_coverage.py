"""
Diff coverage checking functionality.
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path
import subprocess
from typing import Set, List, Dict, Tuple, Optional
from .config import IntegrityConfig


class DiffCoverageChecker:
    """Check diff coverage against coverage.xml and fail if below threshold."""
    
    def __init__(self, config: Optional[IntegrityConfig] = None):
        """Initialize diff coverage checker.
        
        Args:
            config: Configuration for diff coverage checks
        """
        self.config = config or IntegrityConfig()
    
    def get_diff_files(self) -> Set[str]:
        """Get list of files changed in current diff.
        
        Returns:
            Set of changed Python file paths
        """
        try:
            # Get merge base with origin/main
            result = subprocess.run(
                ["git", "merge-base", "HEAD", "origin/main"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                merge_base = result.stdout.strip()
                # Get diff against merge base
                result = subprocess.run(
                    ["git", "diff", "--name-only", merge_base],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if result.returncode == 0:
                    files = result.stdout.strip().split('\n')
                    return {f for f in files if f and f.endswith('.py')}
        except Exception:
            pass
        
        try:
            # Fallback to origin/main diff
            result = subprocess.run(
                ["git", "diff", "--name-only", "origin/main"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                files = result.stdout.strip().split('\n')
                return {f for f in files if f and f.endswith('.py')}
        except Exception:
            pass
        
        try:
            # Fallback to staged changes
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                files = result.stdout.strip().split('\n')
                return {f for f in files if f and f.endswith('.py')}
        except Exception:
            pass
        
        # Fallback to working directory changes
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                files = result.stdout.strip().split('\n')
                return {f for f in files if f and f.endswith('.py')}
        except Exception:
            pass
        
        return set()
    
    def parse_coverage_xml(self, coverage_file: str = "coverage.xml") -> Dict[str, Set[int]]:
        """Parse coverage.xml and return coverage data.
        
        Args:
            coverage_file: Path to coverage.xml file
            
        Returns:
            Dict mapping file paths to sets of covered line numbers
        """
        if not Path(coverage_file).exists():
            raise FileNotFoundError(f"Coverage file {coverage_file} not found")
        
        tree = ET.parse(coverage_file)
        root = tree.getroot()
        
        coverage_data = {}
        for package in root.findall('.//package'):
            for class_elem in package.findall('.//class'):
                filename = class_elem.get('filename')
                if filename:
                    lines = class_elem.findall('.//line')
                    covered_lines = {int(line.get('number')) for line in lines if line.get('hits') != '0'}
                    coverage_data[filename] = covered_lines
        
        return coverage_data
    
    def get_changed_lines(self, file_path: str) -> Set[int]:
        """Get changed line numbers for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Set of changed line numbers
        """
        changed_lines = set()
        
        try:
            # Try merge-base diff first
            result = subprocess.run(
                ["git", "merge-base", "HEAD", "origin/main"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                merge_base = result.stdout.strip()
                result = subprocess.run(
                    ["git", "diff", merge_base, "--unified=0", file_path],
                    capture_output=True,
                    text=True,
                    check=False
                )
            else:
                # Fallback to origin/main diff
                result = subprocess.run(
                    ["git", "diff", "origin/main", "--unified=0", file_path],
                    capture_output=True,
                    text=True,
                    check=False
                )
            
            if result.returncode != 0:
                # Try working directory diff as fallback
                result = subprocess.run(
                    ["git", "diff", "--unified=0", file_path],
                    capture_output=True,
                    text=True,
                    check=False
                )
            
            # Parse diff to get changed line numbers
            current_line = 0
            
            for line in result.stdout.split('\n'):
                if line.startswith('@@'):
                    # Parse @@ -old_start,old_count +new_start,new_count @@
                    parts = line.split(' ')
                    if len(parts) >= 3:
                        new_part = parts[2]
                        if new_part.startswith('+'):
                            try:
                                start_line = int(new_part[1:].split(',')[0])
                                current_line = start_line
                            except (ValueError, IndexError):
                                pass
                elif line.startswith('+') and not line.startswith('+++'):
                    # This is an added line
                    changed_lines.add(current_line)
                    current_line += 1
                elif line.startswith('-') and not line.startswith('---'):
                    # This is a deleted line, skip
                    pass
                else:
                    # Context line, increment counter
                    current_line += 1
                    
        except subprocess.CalledProcessError:
            pass
        
        return changed_lines
    
    def check_diff_coverage(self, diff_files: Set[str], coverage_data: Dict[str, Set[int]]) -> Tuple[bool, List[str]]:
        """Check if all changed lines in diff files are covered.
        
        Args:
            diff_files: Set of changed file paths
            coverage_data: Coverage data from coverage.xml
            
        Returns:
            Tuple of (is_covered, uncovered_lines)
        """
        uncovered_lines = []
        
        for file_path in diff_files:
            if file_path not in coverage_data:
                # Handle renames/moved code - check if file exists with different path
                found_file = None
                for covered_file in coverage_data.keys():
                    if Path(covered_file).name == Path(file_path).name:
                        found_file = covered_file
                        break
                
                if found_file:
                    file_path = found_file
                else:
                    continue
            
            # Get changed lines for this file
            changed_lines = self.get_changed_lines(file_path)
            
            # Check if changed lines are covered
            covered_lines = coverage_data.get(file_path, set())
            file_uncovered = [f"{file_path}:{line}" for line in changed_lines if line not in covered_lines]
            uncovered_lines.extend(file_uncovered)
        
        return len(uncovered_lines) == 0, uncovered_lines
    
    def check(self, coverage_file: str = "coverage.xml") -> Tuple[bool, List[str]]:
        """Run diff coverage check.
        
        Args:
            coverage_file: Path to coverage.xml file
            
        Returns:
            Tuple of (success, violations)
        """
        violations = []
        
        # Get diff files
        diff_files = self.get_diff_files()
        if not diff_files:
            return True, violations
        
        # Parse coverage data
        try:
            coverage_data = self.parse_coverage_xml(coverage_file)
        except FileNotFoundError as e:
            violations.append(str(e))
            return False, violations
        
        # Check diff coverage
        is_covered, uncovered_lines = self.check_diff_coverage(diff_files, coverage_data)
        
        if not is_covered:
            violations.append(f"Diff coverage below {self.config.min_diff_coverage}%")
            violations.extend([f"Uncovered line: {line}" for line in uncovered_lines])
        
        return is_covered, violations 