"""
Configuration for integrity gates.
"""

from dataclasses import dataclass
from typing import Optional, List
import os


@dataclass
class IntegrityConfig:
    """Configuration for integrity gates."""
    
    # Coverage settings
    min_coverage: float = 80.0
    min_diff_coverage: float = 100.0
    
    # Test settings
    allow_trivial_tests: bool = False
    trivial_test_patterns: List[str] = None
    
    # Policy settings
    policy_file: Optional[str] = None
    policy_rules: List[str] = None
    
    # Observer settings
    observer_enabled: bool = True
    observer_log_file: Optional[str] = None
    
    # Tamper settings
    tamper_check_enabled: bool = True
    tamper_whitelist: List[str] = None
    
    def __post_init__(self):
        """Set defaults after initialization."""
        if self.trivial_test_patterns is None:
            self.trivial_test_patterns = [
                "def test_",
                "class Test",
                "pytest.raises",
                "pytest.mark.parametrize"
            ]
        
        if self.policy_rules is None:
            self.policy_rules = [
                "coverage >= 80%",
                "no_skipped_tests",
                "no_trivial_tests"
            ]
        
        if self.tamper_whitelist is None:
            self.tamper_whitelist = [
                "coverage.xml",
                ".coverage",
                "htmlcov/",
                ".pytest_cache/"
            ]
    
    @classmethod
    def from_env(cls) -> "IntegrityConfig":
        """Create config from environment variables."""
        return cls(
            min_coverage=float(os.getenv("MIN_COVERAGE", "80.0")),
            min_diff_coverage=float(os.getenv("MIN_DIFF_COVERAGE", "100.0")),
            allow_trivial_tests=os.getenv("ALLOW_TRIVIAL_TESTS", "false").lower() == "true",
            policy_file=os.getenv("POLICY_FILE"),
            observer_enabled=os.getenv("OBSERVER_ENABLED", "true").lower() == "true",
            observer_log_file=os.getenv("OBSERVER_LOG_FILE"),
            tamper_check_enabled=os.getenv("TAMPER_CHECK_ENABLED", "true").lower() == "true"
        ) 