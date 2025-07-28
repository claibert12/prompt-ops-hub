from typing import List, Any, Optional

class PolicyViolation:
    def __init__(self, type: str, message: str, severity: str = 'error'):
        self.type = type
        self.message = message
        self.severity = severity
    def __repr__(self):
        return f"PolicyViolation(type={self.type}, message={self.message}, severity={self.severity})"

class PolicyResult:
    def __init__(self, allowed: bool, violations: List[Any], error: Optional[str] = None):
        self.allowed = allowed
        self.violations = violations
        self.error = error

# This fallback is used if OPA is unavailable. It enforces the same rules in Python.
def evaluate_policy_fallback(context: dict) -> PolicyResult:
    violations = []
    # coverage
    coverage = context.get('coverage', 0)
    if coverage < 80:
        violations.append(PolicyViolation('coverage', f'Coverage {coverage}% < 80%', 'error'))
    # diff coverage
    diff_coverage = context.get('diff_coverage', 0)
    if diff_coverage < 100:
        violations.append(PolicyViolation('diff_coverage', f'Diff coverage {diff_coverage}% < 100%', 'error'))
    # test deletions
    test_deletions = context.get('test_deletions', False)
    if test_deletions:
        violations.append(PolicyViolation('test_deletions', 'Test deletions detected without #TEST_CHANGE', 'error'))
    # threshold lowering
    threshold_lowered = context.get('threshold_lowered', False)
    if threshold_lowered:
        violations.append(PolicyViolation('threshold_lowered', 'Coverage/test threshold lowered', 'error'))
    # integrity score
    integrity_score = context.get('integrity_score', 100)
    if integrity_score < 70:
        violations.append(PolicyViolation('integrity_score', f'Integrity score {integrity_score} < 70', 'error'))
    allowed = len(violations) == 0
    return PolicyResult(allowed, violations) 