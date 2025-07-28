"""Prompt builder for Prompt Ops Hub."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .config import config_loader


class PromptBuilder:
    """Builds prompts from templates with injected context."""

    def __init__(self, templates_dir: str = None):
        """Initialize prompt builder.
        
        Args:
            templates_dir: Path to templates directory. Defaults to ./templates
        """
        if templates_dir is None:
            # Find templates directory relative to this file
            current_dir = Path(__file__).parent
            templates_dir = current_dir.parent.parent / "templates"

        self.templates_dir = Path(templates_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )

    def build_task_prompt(self, task_description: str) -> str:
        """Build a task prompt with injected context.
        
        Args:
            task_description: Description of the task to execute
            
        Returns:
            Rendered prompt with context
            
        Raises:
            FileNotFoundError: If task_prompt.jinja template doesn't exist
            jinja2.TemplateError: If template rendering fails
        """
        # Load configuration
        config = config_loader.get_all_config()

        # Prepare template context
        context = {
            "task_description": task_description,
            "rules_excerpt": config["rules_excerpt"],
            "context_excerpt": config["context_excerpt"],
            "phase": config["phase"],
        }

        # Render template
        template = self.env.get_template("task_prompt.jinja")
        return template.render(**context)

    def build_custom_prompt(self, template_name: str, **context) -> str:
        """Build a custom prompt from a template.
        
        Args:
            template_name: Name of the template file
            **context: Template context variables
            
        Returns:
            Rendered prompt
            
        Raises:
            FileNotFoundError: If template doesn't exist
            jinja2.TemplateError: If template rendering fails
        """
        template = self.env.get_template(template_name)
        return template.render(**context)

    def get_available_templates(self) -> list[str]:
        """Get list of available template files.
        
        Returns:
            List of template filenames
        """
        if not self.templates_dir.exists():
            return []

        return [
            f.name for f in self.templates_dir.glob("*.jinja")
            if f.is_file()
        ]


# Global prompt builder instance
prompt_builder = PromptBuilder()
