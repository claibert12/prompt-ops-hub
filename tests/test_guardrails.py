"""Tests for guardrails functionality."""

from src.core.guardrails import Guardrails, Violation, ViolationType


class TestGuardrails:
    """Test guardrails functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.guardrails = Guardrails(max_diff_size=300)

    def test_check_secrets_in_code(self):
        """Test secret detection in code."""
        code_with_secret = """
def connect_to_api():
    api_key = "sk-1234567890abcdef"
    password = "secret123"
    return api_client
"""
        violations = self.guardrails.check_code(code_with_secret)

        assert len(violations) >= 2
        secret_violations = [v for v in violations if v.type == ViolationType.SECRETS_DETECTED]
        assert len(secret_violations) >= 2
        assert any("api_key" in v.message for v in secret_violations)
        assert any("password" in v.message for v in secret_violations)

    def test_check_hardcoded_urls(self):
        """Test hardcoded URL detection."""
        code_with_urls = """
def fetch_data():
    url = "https://api.example.com/data"
    ws_url = "ws://localhost:8080"
    return requests.get(url)
"""
        violations = self.guardrails.check_code(code_with_urls)

        url_violations = [v for v in violations if v.type == ViolationType.HARDCODED_URLS]
        assert len(url_violations) >= 2
        assert any("https://" in v.message for v in url_violations)
        assert any("ws://" in v.message for v in url_violations)

    def test_check_diff_size(self):
        """Test diff size checking."""
        # Create a large diff
        large_diff = "\n".join([f"line {i}" for i in range(400)])

        violations = self.guardrails.check_diff(large_diff)

        size_violations = [v for v in violations if v.type == ViolationType.DIFF_TOO_LARGE]
        assert len(size_violations) == 1
        assert "400 lines" in size_violations[0].message

    def test_check_acceptance_criteria(self):
        """Test acceptance criteria detection."""
        prompt_with_criteria = """
# Task: Implement feature

## Acceptance Criteria
- Feature works correctly
- Tests pass
"""
        violations = self.guardrails.check_prompt(prompt_with_criteria)
        criteria_violations = [v for v in violations if v.type == ViolationType.MISSING_ACCEPTANCE_CRITERIA]
        assert len(criteria_violations) == 0
        assert isinstance(violations, list)

    def test_check_missing_acceptance_criteria(self):
        """Test missing acceptance criteria detection."""
        prompt_without_criteria = """
# Task: Implement feature

This is a task without acceptance criteria.
"""
        violations = self.guardrails.check_prompt(prompt_without_criteria)
        criteria_violations = [v for v in violations if v.type == ViolationType.MISSING_ACCEPTANCE_CRITERIA]
        assert len(criteria_violations) == 1
        assert isinstance(violations, list)

    def test_check_tests_mention(self):
        """Test tests mention detection."""
        prompt_with_tests = """
# Task: Implement feature

Make sure to write tests for this feature.
"""
        violations = self.guardrails.check_prompt(prompt_with_tests)
        test_violations = [v for v in violations if v.type == ViolationType.NO_TESTS]
        assert len(test_violations) == 0
        assert isinstance(violations, list)

    def test_check_missing_tests_mention(self):
        """Test missing tests mention detection."""
        prompt_without_tests = """
# Task: Implement feature

This task doesn't mention testing at all.
"""
        violations = self.guardrails.check_prompt(prompt_without_tests)
        test_violations = [v for v in violations if v.type == ViolationType.NO_TESTS]
        assert len(test_violations) == 1
        assert isinstance(violations, list)

    def test_should_block_execution(self):
        """Test execution blocking logic."""
        # No violations
        violations = []
        assert not self.guardrails.should_block_execution(violations)

        # Warning violations only
        warning_violations = [
            Violation(ViolationType.HARDCODED_URLS, "URL found", severity="warning")
        ]
        assert not self.guardrails.should_block_execution(warning_violations)

        # Critical violations
        critical_violations = [
            Violation(ViolationType.SECRETS_DETECTED, "Secret found", severity="critical")
        ]
        assert self.guardrails.should_block_execution(critical_violations)

        # Mixed violations
        mixed_violations = [
            Violation(ViolationType.HARDCODED_URLS, "URL found", severity="warning"),
            Violation(ViolationType.SECRETS_DETECTED, "Secret found", severity="critical")
        ]
        assert self.guardrails.should_block_execution(mixed_violations)

    def test_get_violation_summary(self):
        """Test violation summary generation."""
        # No violations
        violations = []
        summary = self.guardrails.get_violation_summary(violations)
        assert "✅ No violations detected" in summary

        # With violations
        violations = [
            Violation(ViolationType.SECRETS_DETECTED, "Secret found", line_number=5, severity="critical"),
            Violation(ViolationType.HARDCODED_URLS, "URL found", line_number=10, severity="warning")
        ]
        summary = self.guardrails.get_violation_summary(violations)
        assert "⚠️  2 violation(s) detected:" in summary
        assert "CRITICAL: Secret found (line 5)" in summary
        assert "WARNING: URL found (line 10)" in summary

    def test_check_semgrep_results(self):
        """Test semgrep results integration."""
        semgrep_results = {
            "success": True,
            "findings": [
                {
                    "extra": {
                        "severity": "HIGH",
                        "message": "Dangerous eval() usage",
                        "metadata": {"category": "security"}
                    },
                    "path": "src/test.py",
                    "start": {"line": 42}
                },
                {
                    "extra": {
                        "severity": "MEDIUM",
                        "message": "Performance issue",
                        "metadata": {"category": "performance"}
                    },
                    "path": "src/slow.py",
                    "start": {"line": 15}
                }
            ]
        }

        violations = self.guardrails.check_semgrep_results(semgrep_results)

        assert len(violations) == 2
        
        # Check security violation
        security_violations = [v for v in violations if v.type == ViolationType.SEMGREP_SECURITY]
        assert len(security_violations) == 1
        assert security_violations[0].severity == "critical"
        assert "eval()" in security_violations[0].message
        
        # Check performance violation
        perf_violations = [v for v in violations if v.type == ViolationType.SEMGREP_PERFORMANCE]
        assert len(perf_violations) == 1
        assert perf_violations[0].severity == "error"
        assert "Performance issue" in perf_violations[0].message

    def test_check_policy_results(self):
        """Test policy results integration."""
        policy_results = {
            "allowed": False,
            "violations": ["diff_too_large", "missing_acceptance_criteria"]
        }

        violations = self.guardrails.check_policy_results(policy_results)

        assert len(violations) == 2
        assert all(v.type == ViolationType.POLICY_VIOLATION for v in violations)
        assert all(v.severity == "error" for v in violations)
        assert any("diff_too_large" in v.message for v in violations)
        assert any("missing_acceptance_criteria" in v.message for v in violations)

    def test_check_dependency_results(self):
        """Test dependency scan results integration."""
        dep_results = {
            "success": True,
            "vulnerabilities": [
                {
                    "severity": "CRITICAL",
                    "package": {"name": "requests", "version": "2.25.1"},
                    "description": "Critical CVE-2021-33503"
                },
                {
                    "severity": "HIGH",
                    "package": {"name": "urllib3", "version": "1.26.5"},
                    "description": "High severity CVE-2021-33503"
                }
            ]
        }

        violations = self.guardrails.check_dependency_results(dep_results)

        assert len(violations) == 2
        assert all(v.type == ViolationType.DEPENDENCY_CVE for v in violations)
        
        # Check critical violation
        critical_violations = [v for v in violations if v.severity == "critical"]
        assert len(critical_violations) == 2  # Both CRITICAL and HIGH map to critical
        assert any("requests@2.25.1" in v.message for v in critical_violations)
        assert any("urllib3@1.26.5" in v.message for v in critical_violations)

    def test_check_all_integration(self):
        """Test integration of all guardrails checks."""
        # Mock results
        semgrep_results = {
            "success": True,
            "findings": [
                {
                    "extra": {
                        "severity": "HIGH",
                        "message": "Security issue",
                        "metadata": {"category": "security"}
                    },
                    "path": "src/test.py",
                    "start": {"line": 10}
                }
            ]
        }
        
        policy_results = {
            "allowed": False,
            "violations": ["diff_too_large"]
        }
        
        dep_results = {
            "success": True,
            "vulnerabilities": [
                {
                    "severity": "CRITICAL",
                    "package": {"name": "test-pkg", "version": "1.0.0"},
                    "description": "Critical vulnerability"
                }
            ]
        }

        violations = self.guardrails.check_all(
            diff_str="+ def test():\n+     pass",
            prompt="Test prompt",
            code="password = 'secret'",
            semgrep_results=semgrep_results,
            policy_results=policy_results,
            dep_results=dep_results
        )

        # Should have violations from all sources
        assert len(violations) > 0
        
        # Check for specific violation types
        semgrep_violations = [v for v in violations if v.type == ViolationType.SEMGREP_SECURITY]
        policy_violations = [v for v in violations if v.type == ViolationType.POLICY_VIOLATION]
        dep_violations = [v for v in violations if v.type == ViolationType.DEPENDENCY_CVE]
        secret_violations = [v for v in violations if v.type == ViolationType.SECRETS_DETECTED]
        
        assert len(semgrep_violations) >= 1
        assert len(policy_violations) >= 1
        assert len(dep_violations) >= 1
        assert len(secret_violations) >= 1
