# Rego policy rules for Prompt Ops Hub
# These rules evaluate code changes and enforce project policies

package promptops.policy

# Default decision is to allow
default allow = false

# Allow if all policy checks pass
allow {
    not has_violations
}

# Check for violations
has_violations {
    violations[_]
}

# Violation: Diff too large (> 300 LOC)
violations["diff_too_large"] {
    input.diff_loc > 300
}

# Violation: Missing acceptance criteria
violations["missing_acceptance_criteria"] {
    not has_acceptance_criteria
}

# Check if acceptance criteria are present
has_acceptance_criteria {
    input.acceptance_criteria
    count(input.acceptance_criteria) > 0
}

# Violation: New external dependencies without justification
violations["new_external_deps"] {
    has_new_dependencies
    not has_dependency_justification
}

# Check if new dependencies were added
has_new_dependencies {
    input.new_dependencies
    count(input.new_dependencies) > 0
}

# Check if dependencies have justification
has_dependency_justification {
    input.dependency_justification
    count(input.dependency_justification) > 0
}

# Violation: Security issues detected
violations["security_issues"] {
    input.security_findings
    count(input.security_findings) > 0
}

# Violation: Performance issues detected
violations["performance_issues"] {
    input.performance_findings
    count(input.performance_findings) > 0
}

# Violation: Missing tests
violations["missing_tests"] {
    not has_tests
}

# Check if tests are present
has_tests {
    input.test_files
    count(input.test_files) > 0
}

# Violation: Large files (> 1000 LOC)
violations["large_files"] {
    input.large_files
    count(input.large_files) > 0
}

# Violation: Hardcoded secrets
violations["hardcoded_secrets"] {
    input.secret_findings
    count(input.secret_findings) > 0
}

# INTEGRITY RULES - New violations for quality gates

# Violation: Coverage threshold too low (< 80%)
violations["coverage_threshold_low"] {
    input.coverage_threshold
    input.coverage_threshold < 80
}

# Violation: Coverage below 80%
violations["coverage_below_80"] {
    input.current_coverage
    input.current_coverage < 80
}

# Violation: Coverage threshold lowered from baseline
violations["coverage_threshold_lowered"] {
    input.coverage_threshold
    input.baseline_threshold
    input.coverage_threshold < input.baseline_threshold
}

# Violation: Test/config changes without #TEST_CHANGE marker
violations["test_changes_unmarked"] {
    input.test_changes
    count(input.test_changes) > 0
    not has_test_change_marker
}

# Violation: Test files deleted without #TEST_CHANGE marker
violations["test_files_deleted"] {
    input.deleted_test_files
    count(input.deleted_test_files) > 0
    not has_test_change_marker
}

# Check if test changes have proper marker
has_test_change_marker {
    input.test_changes
    some change
    change = input.test_changes[_]
    change.marker == "#TEST_CHANGE"
}

# Check if deleted test files have proper marker
has_test_change_marker {
    input.deleted_test_files
    some change
    change = input.deleted_test_files[_]
    change.marker == "#TEST_CHANGE"
}

# Violation: Integrity violations detected
violations["integrity_violations"] {
    input.integrity_violations
    count(input.integrity_violations) > 0
}

# Violation: Integrity score too low
violations["integrity_score_low"] {
    input.integrity_score
    input.integrity_score < 70
}

# Get violation details
violation_details[violation] {
    violations[violation]
}

# Get summary of all violations
summary = {
    "allowed": allow,
    "violations": [v | violations[v]],
    "violation_count": count(violations)
} 