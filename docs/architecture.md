# Architecture

Design decisions and architectural patterns in Orchestrator.

## Overview

Orchestrator is a **standalone project** developed using Amplifier's development framework. It uses pragmatic Python orchestration with Claude Code hooks for logging, following ruthless simplicity and modular design principles.

## Core Principles

### Ruthless Simplicity

- **Manual invocation** - No automated polling complexity
- **Python for orchestration** - Clear, debuggable workflow logic
- **Hooks for logging** - Metrics collection, not orchestration
- **Minimal dependencies** - Only click and pydantic
- **File-based state** - Simple logging, no databases

### Modular Design

- **Clear module boundaries** - models, utils, workflows, CLI
- **~100-150 lines per module** - AI-regeneratable size
- **Pydantic contracts** - Clear data structures
- **Independent testing** - Each module tested in isolation

## Architecture Diagram

```
User Manual Invocation
        ↓
    Click CLI (cli.py)
        ↓
   Workflow (triage.py)
        ↓
    ┌───┴───┬────────┬──────────┐
    ↓       ↓        ↓          ↓
linear-cli  claude  utils   models
    ↓       ↓        ↓          ↓
Fetch   Delegate  Parse    Validate
Ticket  Analysis  JSON     Data
    ↓       ↓        ↓          ↓
    └───┬───┴────────┴──────────┘
        ↓
   Update Linear
        ↓
   Hook (post-execution)
        ↓
   Log Metrics
```

## Module Structure

### Core Python Modules

**models.py** (~100 lines)
- Pydantic data models
- TriageInput, ValidityAnalysis, SeverityAnalysis, TriageResult
- Data validation and serialization

**utils.py** (~150 lines)
- `parse_llm_json()` - Extract JSON from any LLM response
- `retry_cli_command()` - Execute CLI with exponential backoff
- `run_agent()` - Delegate tasks to Claude Code agents

**triage.py** (~150 lines)
- Main workflow orchestration
- Coordinates: fetch → analyze → assess → update
- Error handling and progress reporting

**cli.py** (~80 lines)
- Click CLI interface
- Command routing
- Progress indicators

### Claude Code Hooks

**hook_post_triage.py** (~60 lines)
- Reads workflow result from stdin
- Logs metrics to `logs/triage_metrics.jsonl`
- Returns metadata to stdout (Claude Code protocol)

**hook_logger.py** (~80 lines)
- Shared logging utility (from amplifier)
- File-based logging with timestamps
- Log rotation and cleanup

### Configuration

**pyproject.toml**
- uv-managed dependencies
- Ruff configuration
- Test settings

**Makefile**
- Standard commands (install, check, test, format-sh)
- Consistent with amplifier conventions

## Design Decisions

### Decision: Manual Invocation

**Rationale**: Not all tickets need automated triage. Straightforward tickets are easy to identify manually. Manual invocation is appropriate at this stage.

**User quote**: "Not all tickets that are raised need a tool like this; some are straight-forward and easily identified. The manual triggering by the user with the issue number is perfectly reasonable at this stage."

**Future**: Polling/automation can be added later if needed.

### Decision: Python Orchestration

**Rationale**: Python fills gaps where Claude Code features not intended or not optimal.

**User quote**: "My position is not that we should keep python code to a minimum, but that python should fill gaps where native claude code functional either is not intended to satisfy the need or that it does so in a manner not compatible with our tool."

**Implementation**:
- Click CLI for user interface
- Python workflows for business logic
- Defensive utilities for LLM handling
- Hooks only for logging/metrics

### Decision: Hooks for Logging

**Rationale**: Follow amplifier pattern exactly - hooks are Python scripts that log metrics after workflows complete.

**User quote**: "I would recommend that we review how amplifier leverages hooks as a model to my desire."

**Pattern from amplifier**:
```python
# Hook reads stdin, calls modules, logs outcomes, writes stdout
logger = HookLogger("post_triage")
input_data = json.load(sys.stdin)
# Log metrics...
json.dump({"metadata": {...}}, sys.stdout)
```

### Decision: CLI Tools Over MCP

**Rationale**: CLI tools (linear-cli, gh) are more reliable than MCP servers in user's experience.

**Implementation**:
- `linear-cli` for Linear integration
- `claude code task` for agent delegation
- Subprocess-based, not library imports

### Decision: Defensive Utilities

**Rationale**: LLM responses are natural language, not guaranteed JSON. Need robust parsing.

**Implementation**:
- `parse_llm_json()` - Handles markdown blocks, explanations, malformed JSON
- `retry_cli_command()` - Exponential backoff for transient failures
- Patterns from amplifier's `@DISCOVERIES.md` (lines 442-502)

## Technology Stack

### Python Dependencies

- **click>=8.2.1** - CLI framework
- **pydantic>=2.11.7** - Data validation
- **pydantic-settings>=2.10.1** - Configuration

### Development Tools

- **pytest>=8.3.5** - Testing
- **pytest-asyncio>=0.23.0** - Async test support
- **pytest-cov>=6.1.1** - Coverage reporting
- **pytest-mock>=3.14.0** - Mocking
- **pyright>=1.1.406** - Type checking
- **ruff>=0.11.10** - Linting/formatting

### External Tools

- **uv** - Python package manager
- **pnpm** - Node package manager (for shfmt)
- **shfmt** - Shell script formatter
- **linear-cli** - Linear integration
- **claude** - Claude Code SDK

## Philosophy Alignment

### From IMPLEMENTATION_PHILOSOPHY.md

**Ruthless Simplicity**:
- Start minimal (one workflow)
- Avoid future-proofing (no polling yet)
- Clear over clever (Python over complex patterns)

**Direct Integration**:
- CLI tools as intended (no wrappers)
- Subprocess for isolation
- Defensive patterns where needed

### From MODULAR_DESIGN_PHILOSOPHY.md

**Bricks & Studs**:
- Each module ~100-150 lines
- Clear interfaces (Pydantic models)
- Regeneratable from specs
- Self-contained with tests

**Human Architects, AI Builders**:
- Documentation is specification
- Modules follow clear contracts
- AI can regenerate modules
- Tests validate behavior

## Development Using Amplifier Framework

### Framework Patterns Applied

- **Hooks pattern** - Logging and metrics collection following Amplifier conventions
- **Defensive utilities** - Robust LLM response handling patterns
- **Standard tooling** - uv, ruff, pnpm, shfmt
- **Philosophy** - Ruthless simplicity, modular design
- **Git submodule workspace** - Recommended development setup

### Project Independence

- **Own git repository** - Independent version control
- **Own dependencies** - Own pyproject.toml managed with uv
- **Own license** - MIT License by rzp-labs
- **No code imports** - Clean separation from Amplifier codebase

## Related Documentation

- **[Workflows](workflows.md)** - How workflows work
- **[Adding Workflows](adding_workflows.md)** - Creating new workflows
- **[Hooks & Skills](hooks_and_skills.md)** - Automation patterns
