# Orchestrator

AI-powered orchestrator for tactical product development work.

## Overview

Orchestrator handles tactical product development tasks that typically distract teams from strategic work or slip through the cracks due to volume and context switching. It connects to existing tools (Linear), delegates analysis to specialized AI agents, and learns from outcomes to improve recommendations over time.

**Key capabilities**:
- **Support triage** - Automated validity and severity assessment of Linear tickets
- **Issue investigation** - Research Linear issue history, identify patterns, provide evidence-based recommendations
- **Citation-based findings** - All recommendations cite specific sources with direct links
- **Learning store** - Pattern tracking improves recommendations over time
- **Read-only safe mode** - Test workflows without polluting Linear
- **Metrics collection** - Track workflow performance and success rates

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

### First Investigation

Research issue context and get evidence-based recommendations:

```bash
uv run orchestrator investigate ABC-123
```

The tool researches Linear issue history for similar patterns, synthesizes findings with mandatory citations, and provides recommendations backed by traceable evidence. Results are saved to `investigation_results/ABC-123.md` with full citations.

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

### Issue Investigation

Researches Linear issue history and provides evidence-based recommendations:

1. **Fetch issue** from Linear via GraphQL API
2. **Research Linear history** - Query for similar issues by labels, components, and text patterns
3. **Identify patterns** - AI synthesizes resolution patterns, team expertise, and common paths
4. **Generate recommendations** - Evidence-based suggestions with mandatory citations to source issues
5. **Record patterns** - Learning store tracks pattern → recommendation → outcome for continuous improvement

**Manual invocation**:
```bash
uv run orchestrator investigate <issue-id>
```

**Output**: Saved to `investigation_results/<issue-id>.md` with full citations and direct links to source issues.

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
│   ├── investigation.py   # Investigation workflow
│   ├── linear_history.py  # Linear research module
│   ├── citation_tracker.py # Citation management
│   ├── learning_store.py  # Pattern learning
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

- **Manual invocation** - User triggers workflows explicitly, no automated polling
- **Python orchestration** - Clear, debuggable workflow logic in ~100-150 line modules
- **Hooks for logging** - Metrics collection, not orchestration logic
- **Defensive utilities** - Robust LLM response parsing with retry logic
- **Mandatory citations** - Every finding and recommendation cites specific Linear issues
- **Learning over time** - Pattern store tracks pattern → recommendation → outcome
- **File-based results** - Durable analysis storage in investigation_results/
- **Standard tooling** - uv, ruff, pnpm, shfmt following Amplifier patterns

**[See architecture →](docs/architecture.md)**

## License

MIT License - See [LICENSE](LICENSE)

---

Built following the [Amplifier](https://github.com/microsoft/amplifier) framework for AI-powered development.
