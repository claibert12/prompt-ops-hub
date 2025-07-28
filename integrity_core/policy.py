"""
Policy enforcement functionality.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from .config import IntegrityConfig


class PolicyChecker:
    """Enforce integrity policies."""
    
    def __init__(self, config: Optional[IntegrityConfig] = None):
        """Initialize policy checker.
        
        Args:
            config: Configuration for policy checks
        """
        self.config = config or IntegrityConfig()
        self.policies = self._load_policies()
    
    def _load_policies(self) -> Dict[str, Any]:
        """Load policies from file or use defaults.
        
        Returns:
            Dictionary of policies
        """
        if self.config.policy_file and Path(self.config.policy_file).exists():
            try:
                with open(self.config.policy_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Default policies
        return {
            "coverage": {
                "min_global": 80.0,
                "min_diff": 100.0,
                "enforce_thresholds": True
            },
            "tests": {
                "no_skipped": True,
                "no_trivial": True,
                "require_markers": True
            },
            "security": {
                "no_secrets": True,
                "no_hardcoded_keys": True
            },
            "quality": {
                "no_debug_code": True,
                "no_todos": False
            }
        }
    
    def check_coverage_policy(self, coverage_data: Dict[str, float]) -> List[str]:
        """Check coverage against policies.
        
        Args:
            coverage_data: Coverage data with keys like 'global', 'diff'
            
        Returns:
            List of policy violations
        """
        violations = []
        policies = self.policies.get("coverage", {})
        
        if "global" in coverage_data:
            min_global = policies.get("min_global", 80.0)
            if coverage_data["global"] < min_global:
                violations.append(f"Global coverage {coverage_data['global']}% below policy minimum {min_global}%")
        
        if "diff" in coverage_data:
            min_diff = policies.get("min_diff", 100.0)
            if coverage_data["diff"] < min_diff:
                violations.append(f"Diff coverage {coverage_data['diff']}% below policy minimum {min_diff}%")
        
        return violations
    
    def check_test_policy(self, test_data: Dict[str, Any]) -> List[str]:
        """Check test policies.
        
        Args:
            test_data: Test data with keys like 'skipped', 'trivial'
            
        Returns:
            List of policy violations
        """
        violations = []
        policies = self.policies.get("tests", {})
        
        if policies.get("no_skipped", True) and test_data.get("skipped", 0) > 0:
            violations.append(f"Found {test_data['skipped']} skipped tests (policy: no skipped tests)")
        
        if policies.get("no_trivial", True) and test_data.get("trivial", 0) > 0:
            violations.append(f"Found {test_data['trivial']} trivial tests (policy: no trivial tests)")
        
        return violations
    
    def check_security_policy(self, files: List[str]) -> List[str]:
        """Check security policies.
        
        Args:
            files: List of files to check
            
        Returns:
            List of policy violations
        """
        violations = []
        policies = self.policies.get("security", {})
        
        if policies.get("no_secrets", True):
            # Check for common secret patterns
            secret_patterns = [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']'
            ]
            
            for file_path in files:
                if Path(file_path).exists():
                    try:
                        content = Path(file_path).read_text()
                        for pattern in secret_patterns:
                            import re
                            if re.search(pattern, content, re.IGNORECASE):
                                violations.append(f"Potential secret found in {file_path}")
                                break
                    except (IOError, UnicodeDecodeError):
                        pass
        
        return violations
    
    def check(self, context: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Run all policy checks.
        
        Args:
            context: Context data with coverage, test, and file information
            
        Returns:
            Tuple of (success, violations)
        """
        violations = []
        
        # Check coverage policies
        if "coverage" in context:
            coverage_violations = self.check_coverage_policy(context["coverage"])
            violations.extend(coverage_violations)
        
        # Check test policies
        if "tests" in context:
            test_violations = self.check_test_policy(context["tests"])
            violations.extend(test_violations)
        
        # Check security policies
        if "files" in context:
            security_violations = self.check_security_policy(context["files"])
            violations.extend(security_violations)
        
        return len(violations) == 0, violations 