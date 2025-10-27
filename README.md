# Orchestrator

AI-powered orchestrator for tactical product development work.

## Overview

Orchestrator handles tactical product development tasks that typically distract teams from strategic work or slip through the cracks due to volume and context switching. It connects to existing tools (Linear, Figma, Slack, Notion), uses documentation for context, and delegates analysis to specialized AI agents.

**Key capabilities**:
- Automated triage and analysis of support tickets
- Integration with Linear, Notion, and other tools via CLI
- AI-powered validity and severity assessment
- Read-only codebase access for technical analysis
- Metrics collection for workflow optimization

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) for dependency management
- Linear API key (get from https://linear.app/settings/api)
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) for AI agent delegation

### Installation

```bash
# Install dependencies
cd orchestrator
uv sync

# Verify installation
uv run orchestrator --help
```

### First Triage

Analyze a Linear support ticket:

```bash
uv run orchestrator triage ABC-123
```

The tool fetches the ticket, delegates analysis to AI agents, and updates Linear with validity and severity assessments.

**[See detailed setup →](docs/setup.md)**

## Core Workflows

### Support Triage

Automates investigation of support tickets:

1. **Fetch ticket** from Linear via GraphQL API
2. **Analyze validity** - AI determines if issue is valid and actionable
3. **Assess severity** - AI estimates complexity and priority
4. **Update Linear** - Adds AI analysis as comment, sets priority

**Manual invocation**:
```bash
uv run orchestrator triage <ticket-id>
```

**[Learn more about workflows →](docs/workflows.md)**

## Architecture

Orchestrator is a **standalone git submodule** with pragmatic Python orchestration:

- **Python modules**: CLI, workflow logic, defensive utilities
- **Claude Code hooks**: Logging and metrics (following amplifier pattern)
- **Shell scripts**: Thin wrappers (zsh-compatible)
- **Standard tooling**: uv, ruff, pnpm, shfmt

```
User → CLI → Workflow → External Tools + Agents → Update Ticket
         ↓                                            ↓
    Core Logic                               Hook logs metrics
```

**[See architecture details →](docs/architecture.md)**

## Project Structure

```
orchestrator/
├── src/orchestrator/
│   ├── models.py          # Pydantic domain models
│   ├── utils.py           # Defensive utilities
│   ├── triage.py          # Triage workflow
│   └── cli.py             # Click CLI
├── .claude/tools/         # Claude Code hooks
│   ├── hook_post_triage.py
│   └── hook_logger.py
├── scripts/               # Shell scripts
├── tests/                 # Pytest tests
└── docs/                  # Documentation
```

## Development

### Run Tests

```bash
make test
```

### Lint and Format

```bash
make check        # Lint and type check
make format-sh    # Format shell scripts
```

### Add Dependencies

```bash
# Python dependencies
uv add <package>

# Node dependencies (for shfmt)
pnpm add -D <package>
```

**[See adding workflows →](docs/adding_workflows.md)**

## Documentation

- **[Setup Guide](docs/setup.md)** - Installation and configuration
- **[Workflows](docs/workflows.md)** - Available workflows and usage
- **[Architecture](docs/architecture.md)** - Design decisions and patterns
- **[Adding Workflows](docs/adding_workflows.md)** - Creating new workflows
- **[Hooks & Skills](docs/hooks_and_skills.md)** - Claude Code integration

## Philosophy

Orchestrator follows **ruthless simplicity** and **modular design** principles:

- **Manual invocation first** - No automated polling complexity
- **Python for orchestration** - Clear, debuggable workflow logic
- **Hooks for logging** - Metrics collection, not orchestration
- **Defensive utilities** - Robust LLM response handling
- **Standard tooling** - uv, ruff, pnpm, shfmt

**[See architecture →](docs/architecture.md)**

## License

MIT License - See [LICENSE](LICENSE)

---

Built following the [Amplifier](https://github.com/microsoft/amplifier) framework for AI-powered development.
