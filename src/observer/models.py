"""Observer models for integrity monitoring."""

from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum


class ViolationType(Enum):
    """Types of integrity violations."""
    COVERAGE_DROP = "coverage_drop"
    DIFF_COVERAGE_FAIL = "diff_coverage_fail"
    TEST_SKIPS = "test_skips"
    TEST_DELETIONS = "test_deletions"
    THRESHOLD_EDITS = "threshold_edits"
    CODE_TEST_RATIO = "code_test_ratio"
    WEASEL_WORDS = "weasel_words"
    CLAIM_MISMATCH = "claim_mismatch"


@dataclass
class IntegrityViolation:
    """An integrity violation."""
    type: ViolationType
    message: str
    severity: str  # "warning", "error", "critical"
    weight: float = 1.0
    details: Dict[str, Any] = None


@dataclass
class IntegrityReport:
    """Integrity report for a run."""
    run_id: str
    score: float  # 0-100
    violations: List[IntegrityViolation]
    questions: List[str]
    summary: str
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {} 