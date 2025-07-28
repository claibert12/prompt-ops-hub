"""Guardrails-lite for security and quality checks."""

import re
from dataclasses import dataclass
from enum import Enum


class ViolationType(Enum):
    """Types of violations that can be detected."""
    DIFF_TOO_LARGE = "diff_too_large"
    MISSING_ACCEPTANCE_CRITERIA = "missing_acceptance_criteria"
    SECRETS_DETECTED = "secrets_detected"
    NO_TESTS = "no_tests"
    HARDCODED_URLS = "hardcoded_urls"
    SEMGREP_SECURITY = "semgrep_security"
    SEMGREP_PERFORMANCE = "semgrep_performance"
    POLICY_VIOLATION = "policy_violation"
    DEPENDENCY_CVE = "dependency_cve"
    INTEGRITY_TAMPER = "integrity_tamper"
    COVERAGE_LOWERED = "coverage_lowered"
    TEST_CHANGES_UNMARKED = "test_changes_unmarked"
    TEST_FILES_DELETED = "test_files_deleted"
    POLICY_INTEGRITY_FAIL = "policy_integrity_fail"
    COVERAGE_BELOW_80 = "coverage_below_80"
    DIFF_COVERAGE_BELOW_100 = "diff_coverage_below_100"
    TRIVIAL_TESTS_DETECTED = "trivial_tests_detected"
    INTEGRITY_SCORE_LOW = "integrity_score_low"


@dataclass
class Violation:
    """A detected violation."""
    type: ViolationType
    message: str
    line_number: int | None = None
    severity: str = "warning"  # warning, error, critical


class Guardrails:
    """Lightweight guardrails for code quality and security."""

    def __init__(self, max_diff_size: int = 300):
        """Initialize guardrails.
        
        Args:
            max_diff_size: Maximum allowed diff size in lines
        """
        self.max_diff_size = max_diff_size

        # Secret patterns to detect
        self.secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'key\s*=\s*["\'][^"\']+["\']',
            r'credential\s*=\s*["\'][^"\']+["\']',
            r'private_key\s*=\s*["\'][^"\']+["\']',
            r'access_token\s*=\s*["\'][^"\']+["\']',
        ]

        # Hardcoded URL patterns
        self.url_patterns = [
            r'https?://[^\s"\']+',
            r'ftp://[^\s"\']+',
            r'ws://[^\s"\']+',
            r'wss://[^\s"\']+',
        ]

    def check_diff(self, diff_str: str) -> list[Violation]:
        """Check a diff for violations.
        
        Args:
            diff_str: Unified diff content
            
        Returns:
            List of detected violations
        """
        violations = []

        # Check diff size
        diff_lines = len(diff_str.split('\n'))
        if diff_lines > self.max_diff_size:
            violations.append(Violation(
                type=ViolationType.DIFF_TOO_LARGE,
                message=f"Diff too large: {diff_lines} lines (max: {self.max_diff_size})",
                severity="error"
            ))

        # Check for secrets
        secret_violations = self._check_secrets(diff_str)
        violations.extend(secret_violations)

        # Check for hardcoded URLs
        url_violations = self._check_hardcoded_urls(diff_str)
        violations.extend(url_violations)

        return violations

    def check_prompt(self, prompt: str) -> list[Violation]:
        """Check a prompt for violations.
        
        Args:
            prompt: Generated prompt content
            
        Returns:
            List of detected violations
        """
        violations = []

        # Check for acceptance criteria
        if not self._has_acceptance_criteria(prompt):
            violations.append(Violation(
                type=ViolationType.MISSING_ACCEPTANCE_CRITERIA,
                message="Missing 'Acceptance Criteria' section in prompt",
                severity="warning"
            ))

        # Check for tests mention
        if not self._has_tests_mention(prompt):
            violations.append(Violation(
                type=ViolationType.NO_TESTS,
                message="No mention of tests in prompt",
                severity="warning"
            ))

        return violations

    def check_code(self, code: str) -> list[Violation]:
        """Check code for violations.
        
        Args:
            code: Code content to check
            
        Returns:
            List of detected violations
        """
        violations = []

        # Check for secrets
        secret_violations = self._check_secrets(code)
        violations.extend(secret_violations)

        # Check for hardcoded URLs
        url_violations = self._check_hardcoded_urls(code)
        violations.extend(url_violations)

        return violations

    def _check_secrets(self, content: str) -> list[Violation]:
        """Check for secret patterns in content.
        
        Args:
            content: Content to check
            
        Returns:
            List of secret violations
        """
        violations = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            for pattern in self.secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(Violation(
                        type=ViolationType.SECRETS_DETECTED,
                        message=f"Potential secret detected: {line.strip()}",
                        line_number=i,
                        severity="critical"
                    ))

        return violations

    def _check_hardcoded_urls(self, content: str) -> list[Violation]:
        """Check for hardcoded URLs in content.
        
        Args:
            content: Content to check
            
        Returns:
            List of URL violations
        """
        violations = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            for pattern in self.url_patterns:
                if re.search(pattern, line):
                    violations.append(Violation(
                        type=ViolationType.HARDCODED_URLS,
                        message=f"Hardcoded URL detected: {line.strip()}",
                        line_number=i,
                        severity="warning"
                    ))

        return violations

    def _has_acceptance_criteria(self, prompt: str) -> bool:
        """Check if prompt has acceptance criteria section.
        
        Args:
            prompt: Prompt content
            
        Returns:
            True if acceptance criteria found
        """
        patterns = [
            r'##\s*Acceptance\s*Criteria',
            r'###\s*Acceptance\s*Criteria',
            r'Acceptance\s*Criteria:',
        ]

        for pattern in patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                return True

        return False

    def _has_tests_mention(self, prompt: str) -> bool:
        """Check if prompt mentions tests.
        
        Args:
            prompt: Prompt content
            
        Returns:
            True if tests mentioned
        """
        test_patterns = [
            r'\btest\b',
            r'\btests\b',
            r'\bpytest\b',
            r'\bunittest\b',
            r'\bassert\b',
        ]

        for pattern in test_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                return True

        return False

    def get_violation_summary(self, violations: list[Violation]) -> str:
        """Get a summary of violations.
        
        Args:
            violations: List of violations
            
        Returns:
            Summary string
        """
        if not violations:
            return "✅ No violations detected"

        summary = f"⚠️  {len(violations)} violation(s) detected:\n"

        for violation in violations:
            line_info = f" (line {violation.line_number})" if violation.line_number else ""
            summary += f"  - {violation.severity.upper()}: {violation.message}{line_info}\n"

        return summary

    def should_block_execution(self, violations: list[Violation]) -> bool:
        """Check if violations should block execution.
        
        Args:
            violations: List of violations
            
        Returns:
            True if execution should be blocked
        """
        critical_violations = [v for v in violations if v.severity == "critical"]
        return len(critical_violations) > 0

    def auto_split_large_diff(self, diff_str: str, max_size: int = 300) -> list[str]:
        """Auto-split a large diff into smaller chunks.
        
        Args:
            diff_str: Original diff content
            max_size: Maximum size per chunk
            
        Returns:
            List of smaller diff chunks
        """
        lines = diff_str.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0

        for line in lines:
            # If adding this line would exceed max_size, start a new chunk
            if current_size + 1 > max_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_size = 0

            current_chunk.append(line)
            current_size += 1

        # Add the last chunk if it has content
        if current_chunk:
            chunks.append('\n'.join(current_chunk))

        return chunks

    def check_and_auto_split(self, diff_str: str) -> tuple[list[Violation], list[str]]:
        """Check diff for violations and auto-split if too large.
        
        Args:
            diff_str: Diff content to check
            
        Returns:
            Tuple of (violations, split_chunks)
        """
        violations = self.check_diff(diff_str)
        split_chunks = []

        # Check if diff is too large
        size_violations = [v for v in violations if v.type == ViolationType.DIFF_TOO_LARGE]

        if size_violations:
            # Auto-split the diff
            split_chunks = self.auto_split_large_diff(diff_str, self.max_diff_size)

            # Add TODO comments to each chunk
            for i, chunk in enumerate(split_chunks):
                todo_comment = f"\n# TODO(guardrails): This is part {i+1} of a split diff. Original size: {len(diff_str.split())} lines"
                split_chunks[i] = chunk + todo_comment

        return violations, split_chunks

    def check_semgrep_results(self, semgrep_results: dict) -> list[Violation]:
        """Check semgrep results for violations.
        
        Args:
            semgrep_results: Results from semgrep scan
            
        Returns:
            List of detected violations
        """
        violations = []
        
        if not semgrep_results.get("success", False):
            return violations
        
        findings = semgrep_results.get("findings", [])
        
        for finding in findings:
            extra = finding.get("extra", {})
            severity = extra.get("severity", "MEDIUM")
            message = extra.get("message", "Semgrep finding")
            path = finding.get("path", "unknown")
            line = finding.get("start", {}).get("line", 0)
            
            # Map semgrep severity to our severity
            if severity == "HIGH":
                violation_severity = "critical"
            elif severity == "MEDIUM":
                violation_severity = "error"
            else:
                violation_severity = "warning"
            
            # Determine violation type based on category
            category = extra.get("metadata", {}).get("category", "security")
            if category == "security":
                violation_type = ViolationType.SEMGREP_SECURITY
            elif category == "performance":
                violation_type = ViolationType.SEMGREP_PERFORMANCE
            else:
                violation_type = ViolationType.SEMGREP_SECURITY
            
            violations.append(Violation(
                type=violation_type,
                message=f"{message} ({path}:{line})",
                line_number=line,
                severity=violation_severity
            ))
        
        return violations

    def check_policy_results(self, policy_results: dict) -> list[Violation]:
        """Check policy evaluation results for violations.
        
        Args:
            policy_results: Results from policy evaluation
            
        Returns:
            List of detected violations
        """
        violations = []
        
        if not policy_results.get("allowed", True):
            violations_list = policy_results.get("violations", [])
            
            for violation in violations_list:
                if violation in ["coverage_threshold_low", "coverage_threshold_lowered", "test_changes_unmarked", "test_files_deleted", "integrity_violations"]:
                    violations.append(Violation(
                        type=ViolationType.POLICY_INTEGRITY_FAIL,
                        message=f"Policy integrity violation: {violation}",
                        severity="critical"
                    ))
                else:
                    violations.append(Violation(
                        type=ViolationType.POLICY_VIOLATION,
                        message=f"Policy violation: {violation}",
                        severity="error"
                    ))
        
        return violations

    def check_dependency_results(self, dep_results: dict) -> list[Violation]:
        """Check dependency scan results for violations.
        
        Args:
            dep_results: Results from dependency vulnerability scan
            
        Returns:
            List of detected violations
        """
        violations = []
        
        if not dep_results.get("success", False):
            return violations
        
        vulnerabilities = dep_results.get("vulnerabilities", [])
        
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "MEDIUM")
            package = vuln.get("package", {}).get("name", "unknown")
            version = vuln.get("package", {}).get("version", "unknown")
            description = vuln.get("description", "No description")
            
            # Map vulnerability severity to our severity
            if severity in ["CRITICAL", "HIGH"]:
                violation_severity = "critical"
            elif severity == "MEDIUM":
                violation_severity = "error"
            else:
                violation_severity = "warning"
            
            violations.append(Violation(
                type=ViolationType.DEPENDENCY_CVE,
                message=f"CVE in {package}@{version}: {description}",
                severity=violation_severity
            ))
        
        return violations

    def check_all(self, diff_str: str = "", prompt: str = "", code: str = "", 
                  semgrep_results: dict = None, policy_results: dict = None, 
                  dep_results: dict = None) -> list[Violation]:
        """Run all guardrails checks.
        
        Args:
            diff_str: Unified diff content
            prompt: Generated prompt content
            code: Code content
            semgrep_results: Results from semgrep scan
            policy_results: Results from policy evaluation
            dep_results: Results from dependency scan
            
        Returns:
            List of all detected violations
        """
        violations = []
        
        # Run basic checks
        if diff_str:
            violations.extend(self.check_diff(diff_str))
        
        if prompt:
            violations.extend(self.check_prompt(prompt))
        
        if code:
            violations.extend(self.check_code(code))
        
        # Run static analysis checks
        if semgrep_results:
            violations.extend(self.check_semgrep_results(semgrep_results))
        
        if policy_results:
            violations.extend(self.check_policy_results(policy_results))
        
        if dep_results:
            violations.extend(self.check_dependency_results(dep_results))
        
        return violations


# Global guardrails instance
guardrails = Guardrails()
