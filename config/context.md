# Prompt Ops Hub - Project Context

## Overview
Prompt Ops Hub is a local-first tool for managing AI prompts, executing tasks, and maintaining consistency across AI-assisted development workflows. This MVP focuses on core prompt building, task management, and basic API/CLI interfaces.

## Architecture Principles
- **Local-First**: Everything runs on localhost by default
- **Config-Driven**: Rules, context, and phases loaded from config files
- **Template-Based**: Prompts built from Jinja2 templates with injected context
- **SQLite Storage**: Simple local database for task persistence
- **CLI + API**: Both command-line and HTTP interfaces

## Core Components
1. **Config Loader**: Loads rules.md, context.md, and phase.json
2. **Prompt Builder**: Renders templates with injected context
3. **Model Router**: Routes to appropriate AI models (stub in MVP)
4. **Database Layer**: SQLite with SQLModel for task storage
5. **CLI Interface**: Typer-based command line tool
6. **API Interface**: FastAPI for HTTP access

## Development Phases
- **P0**: Core MVP (current) - basic prompt building and task management
- **P1**: Cursor/Git integrations - adapter for Cursor IDE and GitHub PR creation
- **P2**: Advanced features - guardrails, model routing, failure loops

## Technology Stack
- **Python 3.11+**: Core runtime
- **FastAPI**: Web framework for API
- **Typer**: CLI framework
- **SQLModel**: Database ORM (SQLAlchemy + Pydantic)
- **Jinja2**: Template engine
- **SQLite**: Local database
- **Pytest**: Testing framework

## File Structure
```
prompt-ops-hub/
├── src/                    # Application source
│   ├── main.py            # FastAPI app
│   └── cli.py             # CLI interface
├── core/                   # Core business logic
│   ├── config.py          # Configuration loader
│   ├── prompt_builder.py  # Prompt template rendering
│   ├── models.py          # Database models
│   ├── db.py              # Database operations
│   └── router_stub.py     # Model router (stub)
├── templates/              # Jinja2 templates
│   └── task_prompt.jinja  # Main task prompt template
├── config/                 # Configuration files
│   ├── rules.md           # Hub rules and constraints
│   ├── context.md         # Project context (this file)
│   └── phase.json         # Current development phase
├── tests/                  # Test suite
└── pyproject.toml         # Project configuration
```

## Environment Variables
- `DATABASE_URL`: SQLite database path (default: `sqlite:///./prompt_ops.db`)
- `LOG_LEVEL`: Logging level (default: `INFO`)
- `API_HOST`: API server host (default: `localhost`)
- `API_PORT`: API server port (default: `8000`)

## Security Considerations
- No secrets in git or prompts
- Use environment variables for configuration
- Input sanitization for all user inputs
- SQL injection protection via SQLModel
- XSS protection in template rendering

## Performance Notes
- SQLite for local development (consider PostgreSQL for production)
- Template caching for repeated prompt generation
- Connection pooling for database operations
- Async/await for I/O operations

## Future Enhancements
- Model routing with capability tags
- Cursor IDE integration
- GitHub PR automation
- Advanced guardrails and policy engine
- Multi-tenant support
- Audit logging and metrics
- Static analysis integration 