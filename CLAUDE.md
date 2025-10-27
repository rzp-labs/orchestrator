# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Important: Consult Parent Workspace Context

This project is a **git submodule** within the Amplifier workspace. Before working on tasks:

1. **Read this file first** - Orchestrator-specific instructions
2. **Reference parent workspace** - `@../AGENTS.md` and `@../CLAUDE.md` for shared patterns
3. **Check DISCOVERIES.md** - Both orchestrator and parent workspace versions
4. **Review philosophy docs** - `@../ai_context/IMPLEMENTATION_PHILOSOPHY.md` and `@../ai_context/MODULAR_DESIGN_PHILOSOPHY.md`

## Import Key Context Files

Use the `@` syntax to reference these files:

- `@AGENTS.md` - This project's AI guidance
- `@../AGENTS.md` - Parent workspace AI guidance
- `@../CLAUDE.md` - Parent workspace Claude Code guidance
- `@../DISCOVERIES.md` - Parent workspace discoveries and patterns
- `@../ai_context/IMPLEMENTATION_PHILOSOPHY.md` - Ruthless simplicity philosophy
- `@../ai_context/MODULAR_DESIGN_PHILOSOPHY.md` - Modular design principles
- `@docs/architecture.md` - Orchestrator architecture details
- `@docs/workflows.md` - Workflow specifications

## Project Context

**Orchestrator** is an AI-powered tool for tactical product development work, specifically:
- Automated triage and analysis of Linear support tickets
- Integration with Linear via GraphQL API
- AI-powered validity and severity assessment
- Read-only/write mode control for safe testing

**Key principle**: Manual invocation, file-based results, optional Linear writes.

## Critical Operating Principles

### 1. Git Submodule Awareness

**ALWAYS remember**: This is a standalone project that happens to live in the Amplifier workspace.

- **Work from orchestrator directory** - All commands run from `/Users/stephen/amplifier/orchestrator/`
- **Use local .venv** - NOT parent workspace's `.venv`
- **Independent dependencies** - Managed by `uv` in local `pyproject.toml`
- **Own git history** - Commits are to orchestrator repo, not amplifier

### 2. Write Mode Control

**CRITICAL**: Orchestrator has LINEAR_ENABLE_WRITES flag to prevent accidental writes during development.

**Before testing workflows**:
1. Check current mode: `echo $LINEAR_ENABLE_WRITES`
2. Default is read-only (safe)
3. Only enable writes when intentionally testing Linear integration
4. Analysis always saved to `./triage_results/` regardless of mode

**User feedback**:
- CLI displays mode at start: "Mode: READ-ONLY" or "Mode: WRITE"
- Shows what will happen: "Comments will NOT be added to Linear"
- Confirms outcome: "ℹ Linear writes disabled" or "✓ Posted comment to Linear"

### 3. Defensive Utilities Are Mandatory

**NEVER** parse LLM responses directly. **ALWAYS** use defensive utilities:

```python
# Required pattern
from orchestrator.utils import parse_llm_json, call_agent_with_retry

# Parse any LLM response
result = parse_llm_json(llm_response)

# Call agent with automatic retry
validity = call_agent_with_retry(
    agent_name="analysis-expert",
    task="Analyze ticket",
    data={"ticket": data},
    schema=ValidityAnalysis
)
```

**Why**: LLMs return markdown blocks, explanations, malformed JSON. These utilities handle all cases.

### 4. Module Size Discipline

**Target**: ~100-150 lines per module

**Why**: Modules should be small enough for AI to regenerate from spec in single context window.

**Current modules**:
- `models.py`: 44 lines ✓
- `config.py`: 31 lines ✓
- `file_writer.py`: 56 lines ✓
- `cli.py`: 88 lines ✓
- `utils.py`: 333 lines (acceptable - utility collection)
- `triage.py`: ~150 lines ✓

**When refactoring**: Keep modules small and focused.

### 5. Test After Every Code Change

**CRITICAL**: After making code changes, you MUST:

1. **Run `make check`** - Catches syntax, linting, type errors
2. **Run `make test`** - Runs full test suite with coverage
3. **Test the workflow** - Actually run `uv run orchestrator triage <ticket-id>` in read-only mode
4. **Verify outputs** - Check that analysis files are created correctly

**Why**: Type checking catches obvious errors, but only runtime testing catches:
- Invalid API calls to external libraries
- Configuration errors
- Import errors from circular dependencies
- Linear API integration issues

## Development Commands

All commands run from `/Users/stephen/amplifier/orchestrator/`:

```bash
# Install dependencies (first time or after dependency changes)
make install

# Run checks (ruff + pyright)
make check

# Run tests with coverage
make test

# Format shell scripts
make format-sh

# Run specific test
uv run pytest tests/test_triage.py::test_successful_triage -v

# Test triage workflow (read-only by default)
uv run orchestrator triage ABC-123

# Test with Linear writes enabled
LINEAR_ENABLE_WRITES=true uv run orchestrator triage ABC-123
```

## Working with Workflows

### Current Workflows

**Support Triage** (`uv run orchestrator triage <ticket-id>`):
1. Fetches ticket from Linear via GraphQL API
2. Delegates validity analysis to `analysis-expert` agent
3. Delegates severity assessment to `bug-hunter` agent
4. Saves analysis to `./triage_results/{ticket-id}.md`
5. Updates Linear with comment (only if `LINEAR_ENABLE_WRITES=true`)

**See**: `@docs/workflows.md` for complete specification

### Adding New Workflows

**Reference**: `@docs/adding_workflows.md` for complete guide

**Steps**:
1. Define Pydantic models in `models.py`
2. Create workflow module (`src/orchestrator/my_workflow.py`)
3. Add CLI command in `cli.py`
4. Add tests in `tests/test_my_workflow.py`
5. Document in `docs/workflows.md`

**Pattern to follow**:
- Use `call_agent_with_retry()` for agent delegation
- Use `parse_llm_json()` for response parsing
- Use Pydantic models for validation
- Provide progress feedback to users
- Handle errors gracefully with clear messages

## Code Style and Conventions

### Python

- **Type hints**: Required, including for `self`
- **Imports**: Organized (stdlib, third-party, local)
- **Pydantic**: Use for all domain models and validation
- **Logging**: Use `logging.getLogger(__name__)`, not `print()`
- **Error messages**: Clear and actionable

### Formatting

- **Line length**: 120 characters
- **Quotes**: Double quotes
- **Indentation**: 4 spaces
- **EOF**: Must end with newline

### Module Organization

```python
"""Module docstring explaining purpose."""

import stdlib
import thirdparty

from orchestrator.models import MyModel
from orchestrator.utils import my_util

logger = logging.getLogger(__name__)


def my_function() -> MyModel:
    """Clear docstring with args/returns."""
    pass
```

## Testing Strategy

### Test Types

**Integration tests** (primary):
- Test complete workflows end-to-end
- Mock external APIs (Linear, Claude)
- Verify Pydantic validation and error handling
- See `tests/test_triage.py` for examples

**Unit tests** (secondary):
- Test individual utility functions
- Test defensive parsing edge cases
- See `tests/test_utils.py` for examples

**Manual testing** (required):
- Actually run workflows with real Linear tickets
- Verify file outputs in `./triage_results/`
- Test both read-only and write modes

### Test Fixtures

**Location**: `tests/conftest.py`

**Available fixtures**:
- `enable_linear_writes` - Temporarily enable writes for testing
- `disable_linear_writes` - Ensure writes disabled for testing

**Usage**:
```python
def test_my_workflow(disable_linear_writes):
    # Test implementation
    pass
```

## Common Tasks

### Task: Fix Type Errors

1. Run `make check` to see errors
2. Fix type annotations in affected files
3. Run `make check` again to verify
4. Run `make test` to ensure no regressions

### Task: Add New Agent

**Pattern**:
```python
from orchestrator.utils import call_agent_with_retry
from orchestrator.models import MyAnalysis  # Define Pydantic model first

result = call_agent_with_retry(
    agent_name="my-expert",
    task="Analyze something specific",
    data={"input": input_data},
    schema=MyAnalysis,
    max_retries=3
)
```

### Task: Update Documentation

**After adding features**:
1. Update `docs/workflows.md` if adding workflow
2. Update `docs/architecture.md` if changing design
3. Update `CHANGELOG.md` with changes
4. Update `README.md` if changing user-facing behavior

### Task: Debug Workflow Failure

1. Check `./triage_results/{ticket-id}.md` - Was analysis generated?
2. Check logs - What errors occurred?
3. Enable debug logging: `export LOG_LEVEL=DEBUG`
4. Re-run workflow with verbose output

## File Outputs

**Analysis files**: `./triage_results/{ticket-id}.md`
- Markdown format
- Contains full AI analysis
- Includes metadata footer (timestamp, write mode)
- Created ALWAYS, regardless of write mode

**Git**: Do NOT commit:
- `./triage_results/*.md` (test outputs)
- `logs/*.log` (execution logs)
- `.venv/` (virtual environment)

## Configuration

### Environment Variables

**LINEAR_API_KEY** (required):
- Get from https://linear.app/settings/api
- Used by GraphQL API for authentication

**LINEAR_ENABLE_WRITES** (optional):
- Values: `true`, `1`, `yes` (case-insensitive) = writes enabled
- Default: `false` (read-only mode)
- Controls whether Linear is updated with AI comments

**LOG_LEVEL** (optional):
- Values: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- Default: `INFO`
- Controls logging verbosity

### Where Configuration Lives

**Single source of truth**: `pyproject.toml`

**Read from**:
- Ruff settings: `[tool.ruff]`
- Pyright settings: `[tool.pyright]`
- Test settings: `[tool.pytest.ini_options]`
- Dependencies: `[project.dependencies]`

**DO NOT duplicate** - Read from pyproject.toml when needed.

## Architecture Reference

### Design Decisions

**Manual invocation** (not automated polling):
- Not all tickets need automated triage
- Manual triggering is appropriate at this stage
- Polling can be added later if needed

**File-based results** (always):
- Analysis saved to `./triage_results/` (durable storage)
- Like git local commit (file) vs remote push (Linear)
- Never lose expensive LLM analysis

**Direct GraphQL API** (not CLI wrapper):
- More reliable than CLI tools
- Simpler error handling
- Better performance

**Defensive utilities** (mandatory):
- LLMs don't reliably return pure JSON
- Parse defensively with `parse_llm_json()`
- Retry with feedback via `call_agent_with_retry()`

**Reference**: `@docs/architecture.md` for complete rationale

## Philosophy Reminders

### From Implementation Philosophy

- **Ruthless simplicity** - Start minimal, no future-proofing
- **Direct integration** - Use APIs as intended
- **Trust in emergence** - Complex systems from simple components
- **Present-moment focus** - Handle what's needed now

### From Modular Design Philosophy

- **"Bricks & studs"** - Self-contained modules with clear interfaces
- **Human architects, AI builders** - Define specs, let AI generate code
- **Regenerate, don't patch** - Rewrite whole modules from specs
- **~100-150 lines** - Module size for AI regeneration

## Error Handling Patterns

### External API Failures

```python
from orchestrator.linear_client import fetch_issue

try:
    ticket_data = fetch_issue(ticket_id)
except RuntimeError as e:
    logger.error(f"Linear API failed: {e}")
    return TriageResult(
        success=False,
        error=f"Failed to fetch ticket: {e}"
    )
```

### LLM Response Parsing

```python
from orchestrator.utils import parse_llm_json

try:
    data = parse_llm_json(llm_response)
except ValueError as e:
    logger.error(f"Failed to parse LLM response: {e}")
    # Retry logic or graceful degradation
```

### Pydantic Validation

```python
from pydantic import ValidationError

try:
    validity = ValidityAnalysis(**json_data)
except ValidationError as e:
    logger.error(f"Invalid data structure: {e}")
    # Handle validation failure
```

## Remember

- This is a **git submodule** - work from orchestrator directory
- Use **local .venv** - not parent workspace
- **Write mode defaults to READ-ONLY** - safe for testing
- **Always use defensive utilities** - `parse_llm_json()`, `call_agent_with_retry()`
- **Test after changes** - `make check && make test`
- **Keep modules small** - ~100-150 lines for AI regeneration
- **Follow ruthless simplicity** - no future-proofing

## Next Steps

1. Read `@docs/workflows.md` to understand current workflows
2. Read `@docs/architecture.md` for design decisions
3. Run `make install && make test` to verify setup
4. Try `uv run orchestrator triage ABC-123` in read-only mode
5. Review `./triage_results/` to see output format

---

**For comprehensive context**: Reference parent workspace `@../CLAUDE.md` and `@../AGENTS.md` for broader Amplifier patterns and philosophy.
