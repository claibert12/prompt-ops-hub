"""Observer for integrity monitoring."""

import re
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import yaml

from .models import IntegrityReport, IntegrityViolation, ViolationType


class Observer:
    """Observer for monitoring run integrity."""
    
    def __init__(self, config_path: str = "config/integrity_rules.yml"):
        """Initialize observer with config."""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # Weasel words patterns
        self.weasel_patterns = [
            r'\btemporarily\b',
            r'\bjust to pass\b',
            r'\bquick fix\b',
            r'\bworkaround\b',
            r'\bfor now\b',
            r'\blater\b',
            r'\bTODO\b',
            r'\bFIXME\b'
        ]
    
    def _load_config(self) -> Dict[str, Any]:
        """Load integrity rules config."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        return {
            'min_score': 70,
            'coverage_drop_threshold': 5,
            'code_test_ratio_min': 0.1,
            'weasel_word_penalty': 10
        }
    
    def build_integrity_report(self, run_id: str, run_data: Dict[str, Any]) -> IntegrityReport:
        """Build integrity report for a run."""
        violations = []
        questions = []
        
        # Check coverage drop
        coverage_violation = self._check_coverage_drop(run_data)
        if coverage_violation:
            violations.append(coverage_violation)
            questions.append("Why did coverage drop? Was this intentional?")
        
        # Check diff coverage
        diff_violation = self._check_diff_coverage(run_data)
        if diff_violation:
            violations.append(diff_violation)
            questions.append("Why is diff coverage below 100%? Are new lines tested?")
        
        # Check test skips
        skip_violation = self._check_test_skips(run_data)
        if skip_violation:
            violations.append(skip_violation)
            questions.append("Why are tests being skipped? Is this justified?")
        
        # Check test deletions
        deletion_violation = self._check_test_deletions(run_data)
        if deletion_violation:
            violations.append(deletion_violation)
            questions.append("Why were tests deleted? Was this necessary?")
        
        # Check threshold edits
        threshold_violation = self._check_threshold_edits(run_data)
        if threshold_violation:
            violations.append(threshold_violation)
            questions.append("Why were coverage thresholds changed?")
        
        # Check code/test ratio
        ratio_violation = self._check_code_test_ratio(run_data)
        if ratio_violation:
            violations.append(ratio_violation)
            questions.append("Is the code/test ratio appropriate?")
        
        # Check weasel words
        weasel_violation = self._check_weasel_words(run_data)
        if weasel_violation:
            violations.append(weasel_violation)
            questions.append("Are weasel words indicating rushed or temporary fixes?")
        
        # Check claim vs pytest mismatch
        mismatch_violation = self._check_claim_mismatch(run_data)
        if mismatch_violation:
            violations.append(mismatch_violation)
            questions.append("Why is there a mismatch between claims and actual results?")
        
        # Calculate score
        score = self._calculate_score(violations)
        
        # Generate summary
        summary = self._generate_summary(score, violations)
        
        return IntegrityReport(
            run_id=run_id,
            score=score,
            violations=violations,
            questions=questions,
            summary=summary
        )
    
    def _check_coverage_drop(self, run_data: Dict[str, Any]) -> IntegrityViolation:
        """Check for coverage drop."""
        current_coverage = run_data.get('coverage', 0)
        baseline_coverage = run_data.get('baseline_coverage', 80)
        
        if current_coverage < baseline_coverage - self.config.get('coverage_drop_threshold', 5):
            return IntegrityViolation(
                type=ViolationType.COVERAGE_DROP,
                message=f"Coverage dropped from {baseline_coverage}% to {current_coverage}%",
                severity="critical",
                weight=2.0,
                details={'current': current_coverage, 'baseline': baseline_coverage}
            )
        return None
    
    def _check_diff_coverage(self, run_data: Dict[str, Any]) -> IntegrityViolation:
        """Check diff coverage."""
        diff_coverage = run_data.get('diff_coverage', 100)
        
        if diff_coverage < 100:
            return IntegrityViolation(
                type=ViolationType.DIFF_COVERAGE_FAIL,
                message=f"Diff coverage below 100%: {diff_coverage}%",
                severity="error",
                weight=1.5,
                details={'diff_coverage': diff_coverage}
            )
        return None
    
    def _check_test_skips(self, run_data: Dict[str, Any]) -> IntegrityViolation:
        """Check for test skips."""
        skipped_tests = run_data.get('skipped_tests', 0)
        
        if skipped_tests > 0:
            return IntegrityViolation(
                type=ViolationType.TEST_SKIPS,
                message=f"{skipped_tests} tests skipped",
                severity="warning",
                weight=0.5,
                details={'skipped_count': skipped_tests}
            )
        return None
    
    def _check_test_deletions(self, run_data: Dict[str, Any]) -> IntegrityViolation:
        """Check for test deletions."""
        deleted_tests = run_data.get('deleted_test_files', [])
        
        if deleted_tests:
            return IntegrityViolation(
                type=ViolationType.TEST_DELETIONS,
                message=f"{len(deleted_tests)} test files deleted",
                severity="critical",
                weight=2.0,
                details={'deleted_files': deleted_tests}
            )
        return None
    
    def _check_threshold_edits(self, run_data: Dict[str, Any]) -> IntegrityViolation:
        """Check for threshold edits."""
        threshold_changed = run_data.get('threshold_changed', False)
        
        if threshold_changed:
            return IntegrityViolation(
                type=ViolationType.THRESHOLD_EDITS,
                message="Coverage thresholds were modified",
                severity="critical",
                weight=2.0
            )
        return None
    
    def _check_code_test_ratio(self, run_data: Dict[str, Any]) -> IntegrityViolation:
        """Check code/test ratio."""
        code_lines = run_data.get('code_lines', 0)
        test_lines = run_data.get('test_lines', 0)
        
        if code_lines > 0 and test_lines > 0:
            ratio = test_lines / code_lines
            min_ratio = self.config.get('code_test_ratio_min', 0.1)
            
            if ratio < min_ratio:
                return IntegrityViolation(
                    type=ViolationType.CODE_TEST_RATIO,
                    message=f"Code/test ratio too low: {ratio:.2f} (min: {min_ratio})",
                    severity="warning",
                    weight=0.5,
                    details={'ratio': ratio, 'min_ratio': min_ratio}
                )
        return None
    
    def _check_weasel_words(self, run_data: Dict[str, Any]) -> IntegrityViolation:
        """Check for weasel words."""
        content = run_data.get('content', '')
        found_words = []
        
        for pattern in self.weasel_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            found_words.extend(matches)
        
        if found_words:
            return IntegrityViolation(
                type=ViolationType.WEASEL_WORDS,
                message=f"Found weasel words: {', '.join(set(found_words))}",
                severity="warning",
                weight=0.3,
                details={'found_words': list(set(found_words))}
            )
        return None
    
    def _check_claim_mismatch(self, run_data: Dict[str, Any]) -> IntegrityViolation:
        """Check for claim vs pytest mismatch."""
        claimed_success = run_data.get('claimed_success', False)
        pytest_success = run_data.get('pytest_success', True)
        
        if claimed_success != pytest_success:
            return IntegrityViolation(
                type=ViolationType.CLAIM_MISMATCH,
                message="Claimed success doesn't match pytest results",
                severity="critical",
                weight=2.0,
                details={'claimed': claimed_success, 'actual': pytest_success}
            )
        return None
    
    def _calculate_score(self, violations: List[IntegrityViolation]) -> float:
        """Calculate integrity score (0-100)."""
        if not violations:
            return 100.0
        
        total_penalty = sum(v.weight * self._get_severity_multiplier(v.severity) for v in violations)
        score = max(0, 100 - total_penalty)
        
        return round(score, 1)
    
    def _get_severity_multiplier(self, severity: str) -> float:
        """Get penalty multiplier for severity."""
        multipliers = {
            'warning': 5,
            'error': 10,
            'critical': 20
        }
        return multipliers.get(severity, 10)
    
    def _generate_summary(self, score: float, violations: List[IntegrityViolation]) -> str:
        """Generate summary text."""
        if score >= 90:
            return f"Excellent integrity (score: {score})"
        elif score >= 80:
            return f"Good integrity (score: {score})"
        elif score >= 70:
            return f"Acceptable integrity (score: {score})"
        else:
            return f"Poor integrity (score: {score}) - requires attention"


# Global observer instance
observer = Observer() 