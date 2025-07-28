"""Spec and ambiguity expander for Prompt Ops Hub."""

from dataclasses import dataclass
from enum import Enum


class AmbiguityLevel(Enum):
    """Level of ambiguity in a task."""
    CLEAR = "clear"
    MINOR = "minor"
    MAJOR = "major"
    BLOCKING = "blocking"


@dataclass
class ExpandedSpec:
    """Expanded specification for a task."""
    original_goal: str
    scope_summary: str
    acceptance_criteria: list[str]
    edge_cases: list[str]
    rollback_notes: list[str]
    needs_clarification: bool = False
    clarification_questions: list[str] = None
    ambiguity_level: AmbiguityLevel = AmbiguityLevel.CLEAR


class SpecExpander:
    """Expands ambiguous goals into detailed specifications."""

    def __init__(self):
        """Initialize spec expander."""
        # Keywords that indicate ambiguity
        self.ambiguous_keywords = [
            "maybe", "perhaps", "possibly", "might", "could",
            "somehow", "some way", "better", "improve", "fix",
            "handle", "manage", "deal with", "work with"
        ]

        # Vague terms that need clarification
        self.vague_terms = [
            "user-friendly", "robust", "scalable", "efficient",
            "secure", "fast", "reliable", "maintainable",
            "clean", "good", "proper", "appropriate"
        ]

        # Technical terms that might need specification
        self.technical_terms = [
            "api", "database", "frontend", "backend", "service",
            "component", "module", "function", "class", "method"
        ]

    def expand_task(self, goal: str) -> ExpandedSpec:
        """Expand a task goal into a detailed specification.
        
        Args:
            goal: Original task goal/description
            
        Returns:
            ExpandedSpec with detailed breakdown
        """
        # Check for ambiguity first
        ambiguity_level = self._assess_ambiguity(goal)

        if ambiguity_level in [AmbiguityLevel.MAJOR, AmbiguityLevel.BLOCKING]:
            questions = self._generate_clarification_questions(goal)
            return ExpandedSpec(
                original_goal=goal,
                scope_summary="Goal requires clarification before implementation",
                acceptance_criteria=[],
                edge_cases=[],
                rollback_notes=[],
                needs_clarification=True,
                clarification_questions=questions,
                ambiguity_level=ambiguity_level
            )

        # Expand the specification
        scope_summary = self._generate_scope_summary(goal)
        acceptance_criteria = self._generate_acceptance_criteria(goal)
        edge_cases = self._generate_edge_cases(goal)
        rollback_notes = self._generate_rollback_notes(goal)

        return ExpandedSpec(
            original_goal=goal,
            scope_summary=scope_summary,
            acceptance_criteria=acceptance_criteria,
            edge_cases=edge_cases,
            rollback_notes=rollback_notes,
            needs_clarification=False,
            ambiguity_level=ambiguity_level
        )

    def _assess_ambiguity(self, goal: str) -> AmbiguityLevel:
        """Assess the level of ambiguity in a goal.
        
        Args:
            goal: Task goal to assess
            
        Returns:
            AmbiguityLevel indicating how ambiguous the goal is
        """
        goal_lower = goal.lower()

        # Count ambiguous indicators
        ambiguous_count = sum(1 for keyword in self.ambiguous_keywords if keyword in goal_lower)
        vague_count = sum(1 for term in self.vague_terms if term in goal_lower)

        # Check for very short or very long goals
        word_count = len(goal.split())

        # Check for missing technical context
        has_technical_context = any(term in goal_lower for term in self.technical_terms)

        # Scoring system
        score = 0
        score += ambiguous_count * 2
        score += vague_count * 1
        score += (0 if 5 <= word_count <= 50 else 2)  # Too short or too long
        score += (0 if has_technical_context else 1)  # Missing technical context

        if score >= 5:
            return AmbiguityLevel.BLOCKING
        elif score >= 3:
            return AmbiguityLevel.MAJOR
        elif score >= 1:
            return AmbiguityLevel.MINOR
        else:
            return AmbiguityLevel.CLEAR

    def _generate_clarification_questions(self, goal: str) -> list[str]:
        """Generate clarification questions for ambiguous goals.
        
        Args:
            goal: Ambiguous goal
            
        Returns:
            List of up to 3 crisp clarification questions
        """
        questions = []
        goal_lower = goal.lower()

        # Check for missing technical context
        if not any(term in goal_lower for term in self.technical_terms):
            questions.append("What specific technology/component should this be implemented in? (e.g., API endpoint, database table, UI component)")

        # Check for vague terms
        for term in self.vague_terms:
            if term in goal_lower:
                questions.append(f"What does '{term}' mean in this context? Please provide specific criteria or examples.")
                break

        # Check for ambiguous keywords
        for keyword in self.ambiguous_keywords:
            if keyword in goal_lower:
                questions.append("Can you clarify the scope? What specific outcome do you want to achieve?")
                break

        # Check for missing acceptance criteria
        if not any(word in goal_lower for word in ["test", "verify", "check", "validate"]):
            questions.append("How will we know this is working correctly? What specific tests or validation should be included?")

        # Limit to 3 questions
        return questions[:3]

    def _generate_scope_summary(self, goal: str) -> str:
        """Generate a scope summary for the goal.
        
        Args:
            goal: Task goal
            
        Returns:
            Scope summary
        """
        # Extract key components from the goal
        words = goal.split()

        # Identify action words
        action_words = [word for word in words if word.endswith(('e', 'ing', 'ize', 'ify'))]

        # Identify target components
        target_components = []
        for term in self.technical_terms:
            if term in goal.lower():
                target_components.append(term)

        if target_components:
            scope = f"Implement {', '.join(target_components)} functionality to {goal.lower()}"
        else:
            scope = f"Implement functionality to {goal.lower()}"

        return scope

    def _generate_acceptance_criteria(self, goal: str) -> list[str]:
        """Generate acceptance criteria for the goal.
        
        Args:
            goal: Task goal
            
        Returns:
            List of acceptance criteria
        """
        criteria = []
        goal_lower = goal.lower()

        # Always include basic criteria
        criteria.append("Implementation follows the specified rules and constraints")
        criteria.append("Code changes are properly tested with unit and integration tests")
        criteria.append("No hardcoded secrets or sensitive information")
        criteria.append("Configuration uses environment variables where appropriate")

        # Add specific criteria based on goal content
        if any(word in goal_lower for word in ["api", "endpoint", "service"]):
            criteria.append("API endpoints return appropriate HTTP status codes")
            criteria.append("Input validation is implemented")
            criteria.append("Error handling provides meaningful messages")

        if any(word in goal_lower for word in ["database", "db", "table", "model"]):
            criteria.append("Database schema changes are properly migrated")
            criteria.append("Data integrity is maintained")
            criteria.append("Performance considerations are addressed")

        if any(word in goal_lower for word in ["ui", "frontend", "component", "page"]):
            criteria.append("User interface is responsive and accessible")
            criteria.append("User interactions provide appropriate feedback")
            criteria.append("Error states are handled gracefully")

        if any(word in goal_lower for word in ["test", "testing", "tested"]):
            criteria.append("Test coverage meets project standards")
            criteria.append("Tests are deterministic and reliable")
            criteria.append("Integration tests verify end-to-end functionality")

        return criteria

    def _generate_edge_cases(self, goal: str) -> list[str]:
        """Generate edge cases to consider.
        
        Args:
            goal: Task goal
            
        Returns:
            List of edge cases
        """
        edge_cases = []
        goal_lower = goal.lower()

        # Common edge cases
        edge_cases.append("Empty or null input values")
        edge_cases.append("Very large input values")
        edge_cases.append("Special characters in input")
        edge_cases.append("Concurrent access/modification")

        # Specific edge cases based on goal
        if any(word in goal_lower for word in ["api", "endpoint", "service"]):
            edge_cases.append("Network timeouts and connection failures")
            edge_cases.append("Rate limiting and throttling")
            edge_cases.append("Invalid or malformed requests")

        if any(word in goal_lower for word in ["database", "db", "table"]):
            edge_cases.append("Database connection failures")
            edge_cases.append("Transaction rollbacks")
            edge_cases.append("Data consistency during concurrent operations")

        if any(word in goal_lower for word in ["file", "upload", "download"]):
            edge_cases.append("File size limits")
            edge_cases.append("Invalid file formats")
            edge_cases.append("Disk space limitations")

        return edge_cases

    def _generate_rollback_notes(self, goal: str) -> list[str]:
        """Generate rollback notes for the task.
        
        Args:
            goal: Task goal
            
        Returns:
            List of rollback considerations
        """
        rollback_notes = []
        goal_lower = goal.lower()

        # Always include basic rollback notes
        rollback_notes.append("Database migrations should be reversible")
        rollback_notes.append("Configuration changes should be documented")
        rollback_notes.append("Feature flags should be used for gradual rollout")

        # Specific rollback notes based on goal
        if any(word in goal_lower for word in ["api", "endpoint", "service"]):
            rollback_notes.append("API versioning should be maintained for backward compatibility")
            rollback_notes.append("Client applications should handle API changes gracefully")

        if any(word in goal_lower for word in ["database", "db", "table"]):
            rollback_notes.append("Database backups should be created before schema changes")
            rollback_notes.append("Data migration scripts should be tested in staging")

        if any(word in goal_lower for word in ["deploy", "deployment", "release"]):
            rollback_notes.append("Deployment should be done in stages (dev, staging, prod)")
            rollback_notes.append("Rollback procedures should be documented and tested")

        return rollback_notes


# Global spec expander instance
spec_expander = SpecExpander()
