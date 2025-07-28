"""Configuration loader for Prompt Ops Hub."""

import json
from pathlib import Path
from typing import Any


class ConfigLoader:
    """Loads configuration from config files."""

    def __init__(self, config_dir: str | None = None):
        """Initialize config loader.
        
        Args:
            config_dir: Path to config directory. Defaults to ./config
        """
        if config_dir is None:
            # Find config directory relative to this file
            current_dir = Path(__file__).parent
            config_dir = current_dir.parent.parent / "config"

        self.config_dir = Path(config_dir)

    def load_rules(self) -> str:
        """Load rules from config/rules.md.
        
        Returns:
            Content of rules.md file
            
        Raises:
            FileNotFoundError: If rules.md doesn't exist
        """
        rules_path = self.config_dir / "rules.md"
        if not rules_path.exists():
            raise FileNotFoundError(f"Rules file not found: {rules_path}")

        with open(rules_path, encoding="utf-8") as f:
            return f.read()

    def load_context(self) -> str:
        """Load context from config/context.md.
        
        Returns:
            Content of context.md file
            
        Raises:
            FileNotFoundError: If context.md doesn't exist
        """
        context_path = self.config_dir / "context.md"
        if not context_path.exists():
            raise FileNotFoundError(f"Context file not found: {context_path}")

        with open(context_path, encoding="utf-8") as f:
            return f.read()

    def load_phase(self) -> dict[str, Any]:
        """Load phase configuration from config/phase.json.
        
        Returns:
            Phase configuration as dictionary
            
        Raises:
            FileNotFoundError: If phase.json doesn't exist
            json.JSONDecodeError: If phase.json is invalid JSON
        """
        phase_path = self.config_dir / "phase.json"
        if not phase_path.exists():
            raise FileNotFoundError(f"Phase file not found: {phase_path}")

        with open(phase_path, encoding="utf-8") as f:
            return json.load(f)

    def get_rules_excerpt(self, max_words: int = 300) -> str:
        """Get first N words of rules for prompt injection.
        
        Args:
            max_words: Maximum number of words to include
            
        Returns:
            Excerpt of rules content
        """
        rules = self.load_rules()
        words = rules.split()
        excerpt_words = words[:max_words]
        excerpt = " ".join(excerpt_words)

        if len(words) > max_words:
            excerpt += "..."

        return excerpt

    def get_context_excerpt(self, max_words: int = 300) -> str:
        """Get first N words of context for prompt injection.
        
        Args:
            max_words: Maximum number of words to include
            
        Returns:
            Excerpt of context content
        """
        context = self.load_context()
        words = context.split()
        excerpt_words = words[:max_words]
        excerpt = " ".join(excerpt_words)

        if len(words) > max_words:
            excerpt += "..."

        return excerpt

    def get_all_config(self) -> dict[str, Any]:
        """Load all configuration files.
        
        Returns:
            Dictionary containing rules, context, and phase config
        """
        return {
            "rules": self.load_rules(),
            "context": self.load_context(),
            "phase": self.load_phase(),
            "rules_excerpt": self.get_rules_excerpt(),
            "context_excerpt": self.get_context_excerpt(),
        }
    
    def get_integrity_config(self) -> dict[str, Any]:
        """Get integrity configuration settings.
        
        Returns:
            Dictionary containing integrity settings
        """
        return {
            "min_integrity_score": 70.0,
            "min_integrity_for_auto_pr": 70.0,
            "integrity_violation_weights": {
                "coverage_drop": 15.0,
                "diff_coverage_fail": 20.0,
                "test_skips": 10.0,
                "test_deletions": 25.0,
                "threshold_edits": 25.0,
                "code_test_ratio": 5.0,
                "weasel_words": 5.0,
                "claim_mismatch": 20.0
            }
        }


# Global config loader instance
config_loader = ConfigLoader()
