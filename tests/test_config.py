"""Tests for configuration loader."""

import json
import tempfile
from pathlib import Path

import pytest

from src.core.config import ConfigLoader


class TestConfigLoader:
    """Test cases for ConfigLoader."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary config directory
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)

        # Create test config files
        self.create_test_files()

        # Initialize config loader with test directory
        self.loader = ConfigLoader(str(self.config_dir))

    def create_test_files(self):
        """Create test configuration files."""
        # Create rules.md
        rules_content = """# Test Rules
This is a test rules file.
It contains some basic rules for testing.
"""
        with open(self.config_dir / "rules.md", "w") as f:
            f.write(rules_content)

        # Create context.md
        context_content = """# Test Context
This is a test context file.
It contains project context information.
"""
        with open(self.config_dir / "context.md", "w") as f:
            f.write(context_content)

        # Create phase.json
        phase_data = {
            "current_phase": "P0",
            "phase_name": "Test Phase",
            "description": "Test phase description"
        }
        with open(self.config_dir / "phase.json", "w") as f:
            json.dump(phase_data, f)

    def test_load_rules(self):
        """Test loading rules from rules.md."""
        rules = self.loader.load_rules()
        assert "Test Rules" in rules
        assert "test rules file" in rules

    def test_load_context(self):
        """Test loading context from context.md."""
        context = self.loader.load_context()
        assert "Test Context" in context
        assert "project context information" in context

    def test_load_phase(self):
        """Test loading phase from phase.json."""
        phase = self.loader.load_phase()
        assert phase["current_phase"] == "P0"
        assert phase["phase_name"] == "Test Phase"
        assert phase["description"] == "Test phase description"

    def test_get_rules_excerpt(self):
        """Test getting rules excerpt."""
        excerpt = self.loader.get_rules_excerpt(max_words=5)
        words = excerpt.split()
        assert len(words) <= 5
        assert "Test Rules" in excerpt

    def test_get_context_excerpt(self):
        """Test getting context excerpt."""
        excerpt = self.loader.get_context_excerpt(max_words=5)
        words = excerpt.split()
        assert len(words) <= 5
        assert "Test Context" in excerpt

    def test_get_all_config(self):
        """Test getting all configuration."""
        config = self.loader.get_all_config()

        assert "rules" in config
        assert "context" in config
        assert "phase" in config
        assert "rules_excerpt" in config
        assert "context_excerpt" in config

        assert "Test Rules" in config["rules"]
        assert "Test Context" in config["context"]
        assert config["phase"]["current_phase"] == "P0"

    def test_missing_rules_file(self):
        """Test handling of missing rules file."""
        # Remove rules file
        (self.config_dir / "rules.md").unlink()

        with pytest.raises(FileNotFoundError):
            self.loader.load_rules()

    def test_missing_context_file(self):
        """Test handling of missing context file."""
        # Remove context file
        (self.config_dir / "context.md").unlink()

        with pytest.raises(FileNotFoundError):
            self.loader.load_context()

    def test_missing_phase_file(self):
        """Test handling of missing phase file."""
        # Remove phase file
        (self.config_dir / "phase.json").unlink()

        with pytest.raises(FileNotFoundError):
            self.loader.load_phase()

    def test_invalid_json_phase_file(self):
        """Test handling of invalid JSON in phase file."""
        # Write invalid JSON
        with open(self.config_dir / "phase.json", "w") as f:
            f.write("{ invalid json }")

        with pytest.raises(json.JSONDecodeError):
            self.loader.load_phase()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
