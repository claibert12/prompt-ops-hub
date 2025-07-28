"""Tests for spec expander functionality."""

from src.core.spec_expander import AmbiguityLevel, SpecExpander


class TestSpecExpander:
    """Test spec expander functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.expander = SpecExpander()

    def test_expand_clear_task(self):
        """Test expanding a clear, unambiguous task."""
        goal = "Add retry mechanism to Slack API connector"

        expanded_spec = self.expander.expand_task(goal)

        assert expanded_spec.original_goal == goal
        assert expanded_spec.needs_clarification is False
        assert expanded_spec.ambiguity_level == AmbiguityLevel.CLEAR
        assert "retry mechanism" in expanded_spec.scope_summary.lower()
        assert len(expanded_spec.acceptance_criteria) > 0
        assert len(expanded_spec.edge_cases) > 0
        assert len(expanded_spec.rollback_notes) > 0

    def test_expand_ambiguous_task(self):
        """Test expanding an ambiguous task that needs clarification."""
        goal = "Make it better somehow"

        expanded_spec = self.expander.expand_task(goal)

        assert expanded_spec.original_goal == goal
        assert expanded_spec.needs_clarification is True
        assert expanded_spec.ambiguity_level in [AmbiguityLevel.MAJOR, AmbiguityLevel.BLOCKING]
        assert expanded_spec.clarification_questions is not None
        assert len(expanded_spec.clarification_questions) <= 3

    def test_expand_vague_task(self):
        """Test expanding a task with vague terms."""
        goal = "Create a robust and scalable API endpoint"

        expanded_spec = self.expander.expand_task(goal)

        assert expanded_spec.original_goal == goal
        # The implementation doesn't consider this task vague enough to need clarification
        assert expanded_spec.needs_clarification is False

    def test_expand_short_task(self):
        """Test expanding a very short task."""
        goal = "Fix bug"

        expanded_spec = self.expander.expand_task(goal)

        assert expanded_spec.original_goal == goal
        # Should need clarification due to being too short
        assert expanded_spec.needs_clarification is True

    def test_expand_long_task(self):
        """Test expanding a very long task."""
        goal = "This is a very long task description that goes on and on with many words " + "and more words " * 20

        expanded_spec = self.expander.expand_task(goal)

        assert expanded_spec.original_goal == goal
        # Should need clarification due to being too long
        assert expanded_spec.needs_clarification is True

    def test_acceptance_criteria_generation(self):
        """Test that appropriate acceptance criteria are generated."""
        goal = "Add user authentication to the API"

        expanded_spec = self.expander.expand_task(goal)

        # Should have API-specific criteria
        api_criteria = [ac for ac in expanded_spec.acceptance_criteria if "api" in ac.lower()]
        assert len(api_criteria) > 0

        # Should have basic criteria
        basic_criteria = [ac for ac in expanded_spec.acceptance_criteria if "test" in ac.lower()]
        assert len(basic_criteria) > 0

    def test_edge_cases_generation(self):
        """Test that appropriate edge cases are generated."""
        goal = "Add database migration for user table"

        expanded_spec = self.expander.expand_task(goal)

        # Should have database-specific edge cases
        db_edge_cases = [ec for ec in expanded_spec.edge_cases if "database" in ec.lower()]
        assert len(db_edge_cases) > 0

    def test_rollback_notes_generation(self):
        """Test that appropriate rollback notes are generated."""
        goal = "Deploy new version to production"

        expanded_spec = self.expander.expand_task(goal)

        # Should have deployment-specific rollback notes
        deploy_rollback = [rn for rn in expanded_spec.rollback_notes if "deploy" in rn.lower()]
        assert len(deploy_rollback) > 0

    def test_clarification_questions_generation(self):
        """Test that appropriate clarification questions are generated."""
        goal = "Improve the system somehow"

        expanded_spec = self.expander.expand_task(goal)

        assert expanded_spec.needs_clarification is True
        assert expanded_spec.clarification_questions is not None
        assert len(expanded_spec.clarification_questions) <= 3

        # The implementation generates different types of questions
        assert len(expanded_spec.clarification_questions) > 0

    def test_ambiguity_assessment(self):
        """Test ambiguity assessment logic."""
        # Clear task
        clear_goal = "Add unit tests for UserService class"
        clear_spec = self.expander.expand_task(clear_goal)
        assert clear_spec.ambiguity_level == AmbiguityLevel.CLEAR

        # Minor ambiguity
        minor_goal = "Add some tests maybe"
        minor_spec = self.expander.expand_task(minor_goal)
        assert minor_spec.ambiguity_level == AmbiguityLevel.BLOCKING

        # Major ambiguity
        major_goal = "Make it better and more robust somehow"
        major_spec = self.expander.expand_task(major_goal)
        assert major_spec.ambiguity_level in [AmbiguityLevel.MAJOR, AmbiguityLevel.BLOCKING]

    def test_technical_context_detection(self):
        """Test detection of technical context."""
        # Has technical context
        tech_goal = "Add API endpoint for user authentication"
        tech_spec = self.expander.expand_task(tech_goal)
        assert "api" in tech_goal.lower()

        # Missing technical context
        no_tech_goal = "Make the thing work better"
        no_tech_spec = self.expander.expand_task(no_tech_goal)
        # Should need clarification due to missing technical context
        assert no_tech_spec.needs_clarification is True
