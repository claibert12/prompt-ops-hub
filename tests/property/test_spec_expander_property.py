"""Property-based tests for spec expander using Hypothesis."""

import pytest
from hypothesis import given, strategies as st
from src.core.spec_expander import SpecExpander


class TestSpecExpanderProperty:
    """Property-based tests for SpecExpander."""

    def setup_method(self):
        """Set up spec expander."""
        self.expander = SpecExpander()

    def test_expander_initialized(self):
        """Test that expander can be initialized."""
        assert self.expander is not None

    @given(st.text(min_size=1, max_size=50))
    def test_expand_task_always_returns_expanded_spec(self, goal: str):
        """Property: expand_task always returns an ExpandedSpec."""
        result = self.expander.expand_task(goal)
        assert hasattr(result, 'original_goal')
        assert hasattr(result, 'acceptance_criteria')
        assert isinstance(result.acceptance_criteria, list)

    @given(st.text(min_size=1, max_size=50))
    def test_expand_task_has_acceptance_criteria(self, goal: str):
        """Property: expanded result has acceptance criteria."""
        result = self.expander.expand_task(goal)
        # Should have acceptance criteria (even if empty list for ambiguous goals)
        assert hasattr(result, 'acceptance_criteria')
        assert isinstance(result.acceptance_criteria, list)

    @given(st.text(min_size=1, max_size=50))
    def test_expand_task_has_edge_cases(self, goal: str):
        """Property: expanded result has edge cases."""
        result = self.expander.expand_task(goal)
        assert hasattr(result, 'edge_cases')
        assert isinstance(result.edge_cases, list)

    @given(st.text(min_size=1, max_size=50))
    def test_expand_task_has_rollback_notes(self, goal: str):
        """Property: expanded result has rollback notes."""
        result = self.expander.expand_task(goal)
        assert hasattr(result, 'rollback_notes')
        assert isinstance(result.rollback_notes, list)

    @given(st.text(min_size=1, max_size=50))
    def test_expand_task_has_ambiguity_level(self, goal: str):
        """Property: expanded result has ambiguity level."""
        result = self.expander.expand_task(goal)
        assert hasattr(result, 'ambiguity_level')
        assert result.ambiguity_level is not None 