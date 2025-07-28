"""Tests for prompt builder."""

import json
import tempfile
from pathlib import Path

import pytest

from src.core.prompt_builder import PromptBuilder


class TestPromptBuilder:
    """Test cases for PromptBuilder."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir) / "config"
        self.templates_dir = Path(self.temp_dir) / "templates"

        # Create directories
        self.config_dir.mkdir()
        self.templates_dir.mkdir()

        # Create test files
        self.create_test_files()

        # Initialize prompt builder with test directories
        self.builder = PromptBuilder(str(self.templates_dir))

    def create_test_files(self):
        """Create test configuration and template files."""
        # Create config files
        rules_content = """# Test Rules
This is a test rules file.
It contains some basic rules for testing.
"""
        with open(self.config_dir / "rules.md", "w") as f:
            f.write(rules_content)

        context_content = """# Test Context
This is a test context file.
It contains project context information.
"""
        with open(self.config_dir / "context.md", "w") as f:
            f.write(context_content)

        phase_data = {
            "current_phase": "P0",
            "phase_name": "Test Phase",
            "description": "Test phase description"
        }
        with open(self.config_dir / "phase.json", "w") as f:
            json.dump(phase_data, f)

        # Create template file
        template_content = """# Task: {{ task_description }}

## Context
**Phase**: {{ phase.current_phase }} - {{ phase.phase_name }}
**Description**: {{ phase.description }}

## Rules & Constraints
{{ rules_excerpt }}

## Project Context
{{ context_excerpt }}

## Task Details
{{ task_description }}

## Acceptance Criteria
- [ ] Task implementation follows the specified rules and constraints
- [ ] Code changes are properly tested with unit and integration tests

## Self-Check
Before submitting your response, verify that you have:
1. **Followed all rules** from the rules.md file
2. **Included appropriate tests** for any code changes
"""
        with open(self.templates_dir / "task_prompt.jinja", "w") as f:
            f.write(template_content)

    def test_build_task_prompt(self):
        """Test building a task prompt."""
        # Create a mock config loader
        class MockConfigLoader:
            def get_all_config(self):
                return {
                    "rules_excerpt": "Test rules excerpt",
                    "context_excerpt": "Test context excerpt",
                    "phase": {
                        "current_phase": "P0",
                        "phase_name": "Test Phase",
                        "description": "Test phase description"
                    }
                }

        # Create a new prompt builder with mocked config
        from unittest.mock import patch
        with patch('src.core.prompt_builder.config_loader', MockConfigLoader()):
            # Build prompt
            task_description = "Implement a test feature"
            prompt = self.builder.build_task_prompt(task_description)

            # Verify prompt contains expected sections
            assert "Task: Implement a test feature" in prompt
            assert "**Phase**: P0 - Test Phase" in prompt
            assert "Test rules excerpt" in prompt
            assert "Test context excerpt" in prompt
            assert "Acceptance Criteria" in prompt
            assert "Self-Check" in prompt

    def test_build_custom_prompt(self):
        """Test building a custom prompt."""
        # Create a custom template
        custom_template = """Hello {{ name }}!
Your task is: {{ task }}
"""
        with open(self.templates_dir / "custom.jinja", "w") as f:
            f.write(custom_template)

        # Build custom prompt
        prompt = self.builder.build_custom_prompt(
            "custom.jinja",
            name="Test User",
            task="Test Task"
        )

        assert "Hello Test User!" in prompt
        assert "Your task is: Test Task" in prompt

    def test_get_available_templates(self):
        """Test getting available templates."""
        # Create additional template
        with open(self.templates_dir / "another.jinja", "w") as f:
            f.write("Another template")

        templates = self.builder.get_available_templates()

        assert "task_prompt.jinja" in templates
        assert "another.jinja" in templates
        assert len(templates) == 2

    def test_missing_template(self):
        """Test handling of missing template."""
        with pytest.raises(Exception):  # FileNotFoundError or TemplateNotFound
            self.builder.build_custom_prompt("nonexistent.jinja")

    def test_template_with_variables(self):
        """Test template with missing variables."""
        # Create template with required variables
        template_content = """Task: {{ task_description }}
User: {{ user_name }}
"""
        with open(self.templates_dir / "variables.jinja", "w") as f:
            f.write(template_content)

        # Should work with all variables provided
        prompt = self.builder.build_custom_prompt(
            "variables.jinja",
            task_description="Test task",
            user_name="Test user"
        )

        assert "Task: Test task" in prompt
        assert "User: Test user" in prompt

        # Should work with missing variables (Jinja2 handles this gracefully)
        prompt_missing = self.builder.build_custom_prompt("variables.jinja")
        assert "Task: " in prompt_missing
        assert "User: " in prompt_missing

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
