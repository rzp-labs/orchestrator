# AI Assistant Guidance

This file provides guidance to AI assistants when working with code in this repository.

## Project Overview

Orchestrator is an **AI-powered orchestrator for tactical product development work**. It handles tasks that typically distract teams from strategic work or slip through the cracks due to volume and context switching.

**Key capabilities**:
- Automated triage and analysis of support tickets
- Integration with Linear via GraphQL API
- AI-powered validity and severity assessment
- Read-only/write mode control for safe testing
- Metrics collection for workflow optimization

**Philosophy**: This project follows ruthless simplicity and modular design principles. It's a standalone git submodule developed using the Amplifier framework. For comprehensive context on these principles, see the parent workspace's @../AGENTS.md and @../CLAUDE.md.

## Important: This is a Git Submodule

Orchestrator is a **standalone project** that lives as a git submodule within the Amplifier workspace. This means:

- **Independent version control** - Has its own git repository and history
- **Own dependencies** - Has its own `pyproject.toml` managed with `uv`
- **Own virtual environment** - Uses local `.venv/` (NOT parent workspace's `.venv`)
- **Clean separation** - No code imports from Amplifier (only follows its patterns)

### Virtual Environment Isolation

**CRITICAL**: The Makefile enforces local `.venv` usage to prevent using the parent workspace's environment:

```makefile
export VIRTUAL_ENV :=
export UV_PROJECT_ENVIRONMENT := .venv
```

Always run commands from the orchestrator directory itself, not from the parent workspace.

## Build/Test/Lint Commands

**Prerequisites**: `uv` for Python, `pnpm` for Node packages

- Install dependencies: `make install` (runs `uv sync --all-extras`)
- Run all checks: `make check` (ruff + pyright)
- Run tests: `make test` (pytest with coverage)
- Format shell scripts: `make format-sh`
- Check shell formatting: `make check-sh`
- Clean artifacts: `make clean`

**Add dependencies**:
```bash
cd orchestrator  # Must be in submodule directory
uv add <package>           # Production dependency
uv add --dev <package>     # Development dependency
```

## Code Style Guidelines

- **Line length**: 120 characters (configured in `pyproject.toml`)
- **Python version**: 3.11+ required
- **Type hints**: Use consistently, including for `self` in methods
- **Imports**: Organized by standard lib, third-party, local
- **Data validation**: Use Pydantic for all domain models
- **Error handling**: Comprehensive logging with `logging.getLogger(__name__)`
- **Module size**: Target ~100-150 lines per module (AI-regeneratable)

## Formatting Guidelines

- **Tool**: `ruff` for linting and formatting
- **Quote style**: Double quotes
- **Indentation**: 4 spaces
- **Line endings**: LF (Unix style)
- **EOF**: All files must end with newline
- **Shell scripts**: `shfmt -i 4` (4-space indentation)

## Testing Instructions

**Run all tests with coverage** (default):
```bash
make test
```

**Run specific test file**:
```bash
uv run pytest tests/test_triage.py -v
```

**Run specific test**:
```bash
uv run pytest tests/test_utils.py::test_parse_llm_json -v
```

**Test structure**:
- `conftest.py` - Shared fixtures
- `test_*.py` - Module tests
- Focus on integration tests over unit tests
- Mock external tools (Linear API, Claude agents)

## Write Mode Control

**CRITICAL**: Orchestrator has a read-only mode to prevent accidental Linear writes during development/testing.

**Environment variable**: `LINEAR_ENABLE_WRITES`

**Default**: Disabled (read-only)

**Enable writes**:
```bash
export LINEAR_ENABLE_WRITES=true
uv run orchestrator triage ABC-123  # Will post comment to Linear
```

**Read-only mode** (default):
```bash
# Unset or false
uv run orchestrator triage ABC-123  # Saves to file only, no Linear write
```

**How it works**:
- `config.py` reads environment variable
- `linear_client.py` checks flag before making API calls
- `triage.py` saves analysis to file (always)
- `cli.py` displays mode at start and confirms at end

**Why this matters**:
- Safe testing without polluting Linear
- Expensive LLM analyses preserved even in read-only mode
- Clear user feedback about what will happen

## Defensive Utilities Pattern

**CRITICAL**: LLM responses are unpredictable. Always use defensive utilities from `utils.py`:

### parse_llm_json()

**Problem**: LLMs don't reliably return pure JSON. Common issues:
- Markdown-wrapped JSON (` ```json...``` `)
- Explanatory text before/after JSON
- Nested objects with invalid text between
- Malformed quotes and escaping

**Solution**: `parse_llm_json()` extracts JSON from any format:

```python
# Good: Defensive parsing
from orchestrator.utils import parse_llm_json
result = parse_llm_json(llm_response)

# Bad: Direct parsing (will fail on markdown)
import json
result = json.loads(llm_response)  # Breaks on ```json blocks
```

### call_agent_with_retry()

**Problem**: Agent responses may be malformed or fail validation

**Solution**: Automatic retry with error feedback:

```python
from orchestrator.utils import call_agent_with_retry
from orchestrator.models import ValidityAnalysis

# Automatically retries up to 3 times with error feedback
validity = call_agent_with_retry(
    agent_name="analysis-expert",
    task="Analyze ticket validity",
    data={"ticket": ticket_data},
    schema=ValidityAnalysis,  # Pydantic model for validation
    max_retries=3
)
```

**Pattern from DISCOVERIES.md**: These utilities implement patterns proven reliable in production use.

## Development Workflow

### Adding New Workflows

See `docs/adding_workflows.md` for complete guide.

**Steps**:
1. Define Pydantic models in `models.py`
2. Create workflow module (`src/orchestrator/my_workflow.py`)
3. Add CLI command in `cli.py`
4. Add tests in `tests/test_my_workflow.py`
5. Document in `docs/workflows.md`

**Best practices**:
- Use defensive utilities (`parse_llm_json`, `call_agent_with_retry`)
- Implement retry logic for external API calls
- Provide progress feedback to users
- Handle errors gracefully with clear messages
- Target ~100-150 lines per module

### Module Design Principles

**From MODULAR_DESIGN_PHILOSOPHY.md**:

- **"Bricks & studs"** - Each module is self-contained (~100-150 lines)
- **Clear interfaces** - Pydantic models define contracts
- **Regeneratable** - Modules can be rebuilt from specs by AI
- **Independent testing** - Each module tested in isolation

**Human role**: Define specs and validate behavior, not write code line-by-line.

## Configuration Files

**pyproject.toml** - Single source of truth for:
- Dependencies (managed by `uv`)
- Ruff configuration
- Pyright settings
- Pytest configuration
- Project metadata

**Makefile** - Standard commands that reference pyproject.toml settings

**Never duplicate configuration** - Read from pyproject.toml when needed.

## File Structure

```
orchestrator/
├── src/orchestrator/
│   ├── __init__.py
│   ├── models.py          # Pydantic domain models
│   ├── utils.py           # Defensive utilities
│   ├── config.py          # Environment configuration
│   ├── file_writer.py     # Save analysis to files
│   ├── linear_client.py   # Linear GraphQL API
│   ├── triage.py          # Triage workflow
│   └── cli.py             # Click CLI interface
├── .claude/tools/         # Claude Code hooks
│   ├── hook_post_triage.py
│   └── hook_logger.py
├── tests/                 # Pytest tests
│   ├── conftest.py
│   ├── test_*.py
├── docs/                  # Documentation
│   ├── setup.md
│   ├── workflows.md
│   ├── architecture.md
│   └── adding_workflows.md
├── triage_results/        # Saved analysis files
├── logs/                  # Hook logs and metrics
├── pyproject.toml         # Project config
├── Makefile               # Standard commands
├── AGENTS.md              # This file
├── CLAUDE.md              # Claude Code guidance
└── README.md
```

## Philosophy Alignment

This project implements the core philosophies defined in the parent workspace (@../ai_context/IMPLEMENTATION_PHILOSOPHY.md and @../ai_context/MODULAR_DESIGN_PHILOSOPHY.md). The parent workspace contains the canonical philosophy documentation. Below are key principles as applied to Orchestrator:

### Ruthless Simplicity

- **Manual invocation first** - No automated polling complexity
- **Python for orchestration** - Clear, debuggable workflow logic
- **File-based results** - Durable analysis storage
- **Minimal dependencies** - Only essential packages
- **Direct API integration** - GraphQL without unnecessary wrappers

### Modular Design

- **Clear module boundaries** - models, utils, workflows, CLI
- **~100-150 lines per module** - AI-regeneratable size
- **Pydantic contracts** - Clear data structures
- **Independent testing** - Each module tested in isolation

## Related Documentation

- **[Setup Guide](docs/setup.md)** - Installation and configuration
- **[Workflows](docs/workflows.md)** - Available workflows and usage
- **[Architecture](docs/architecture.md)** - Design decisions and patterns
- **[Adding Workflows](docs/adding_workflows.md)** - Creating new workflows

## License

MIT License - See [LICENSE](LICENSE)

---

**Parent workspace**: This project is developed using the [Amplifier](https://github.com/microsoft/amplifier) framework. See parent workspace `AGENTS.md` and `CLAUDE.md` for broader context on development philosophy and patterns.
