# Setup Guide

Complete setup instructions for Orchestrator.

## Prerequisites

### Required Tools

**Python 3.11+**:
```bash
python --version  # Must be 3.11 or higher
```

**uv** (Python package manager):
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

**linear-cli** (Linear integration):
```bash
# Install linear-cli
npm install -g @linear/cli

# Or via Homebrew (macOS)
brew install linear-cli

# Verify installation
linear-cli --version
```

**Claude Code**:
- Orchestrator uses [Claude Code](https://docs.anthropic.com/en/docs/claude-code) for AI agent delegation
- Install Claude Code following the [official setup guide](https://docs.anthropic.com/en/docs/claude-code/installation)

### Optional Tools

**pnpm** (for shell script formatting):
```bash
# Install pnpm
curl -fsSL https://get.pnpm.io/install.sh | sh

# Verify
pnpm --version
```

**shfmt** (shell script formatter):
```bash
# Installed via pnpm after setup
pnpm install
```

## Installation

### Step 1: Navigate to Orchestrator

```bash
cd amplifier/orchestrator
```

### Step 2: Install Python Dependencies

```bash
# Install all dependencies
uv sync

# Verify installation
uv run orchestrator --help
```

This installs:
- click (CLI framework)
- pydantic (data validation)
- pytest, ruff, pyright (dev tools)

### Step 3: Install Node Dependencies (Optional)

```bash
# For shell script formatting
pnpm install
```

### Step 4: Run Tests

```bash
# Verify everything works
make test
```

## Configuration

### Linear CLI Authentication

Authenticate with Linear:

```bash
# Login to Linear
linear-cli auth login

# Verify authentication
linear-cli me
```

### Environment Variables

Orchestrator uses these environment variables (all optional):

```bash
# Linear configuration
export LINEAR_API_KEY="your-api-key"  # If not using linear-cli auth

# Logging configuration
export ORCHESTRATOR_LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR
```

Add to your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
# Orchestrator configuration
export ORCHESTRATOR_LOG_LEVEL="INFO"
```

## Verification

### Verify Installation

```bash
# Check CLI is accessible
uv run orchestrator --help

# Check dependencies
uv run python -c "import click, pydantic; print('Dependencies OK')"

# Check linear-cli
linear-cli --version
```

### Run First Triage

Test with a real Linear ticket:

```bash
# Replace ABC-123 with actual ticket ID
uv run orchestrator triage ABC-123
```

**Expected output**:
```
Fetching ticket ABC-123...
✓ Ticket fetched

Delegating to analysis-expert...
✓ Validity analysis complete

Delegating to bug-hunter...
✓ Severity assessment complete

Updating Linear ticket...
✓ Ticket updated

✓ Triage complete for ABC-123
```

## Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'orchestrator'`

**Solution**:
```bash
# Ensure you're in the orchestrator directory
cd orchestrator

# Reinstall dependencies
uv sync
```

### Linear CLI Not Found

**Problem**: `linear-cli: command not found`

**Solution**:
```bash
# Install linear-cli globally
npm install -g @linear/cli

# Or via Homebrew
brew install linear-cli

# Verify installation
which linear-cli
```

### Linear Authentication Failed

**Problem**: `Linear API authentication failed`

**Solution**:
```bash
# Re-authenticate
linear-cli auth login

# Verify authentication
linear-cli me

# Check API key (if using environment variable)
echo $LINEAR_API_KEY
```

### Claude Code Not Found

**Problem**: `claude: command not found`

**Solution**:
- Install Claude Code following the [official installation guide](https://docs.anthropic.com/en/docs/claude-code/installation)
- Ensure the `claude` CLI is in your PATH
- Verify with `claude --version`

### Permission Errors

**Problem**: Permission denied errors during installation

**Solution**:
```bash
# Don't use sudo with uv
# uv manages virtual environments automatically

# If using pnpm, ensure it's in your PATH
export PNPM_HOME="$HOME/.local/share/pnpm"
export PATH="$PNPM_HOME:$PATH"
```

## Development Setup

### Enable Development Mode

```bash
# Install with dev dependencies
uv sync --dev

# Install pre-commit hooks (if available)
make install-hooks
```

### Configure IDE

**VS Code**:

Recommended extensions:
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Ruff (charliermarsh.ruff)

Settings (`.vscode/settings.json`):
```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.analysis.typeCheckingMode": "basic",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true
  }
}
```

### Verify Development Setup

```bash
# Run all checks
make check

# Run tests with coverage
make test-cov

# Format shell scripts
make format-sh
```

## Next Steps

- **[Learn about workflows](workflows.md)** - Available workflows and usage
- **[Understand architecture](architecture.md)** - Design and patterns
- **[Add new workflows](adding_workflows.md)** - Extend functionality

## Getting Help

**Issues**: Report bugs or request features via GitHub issues

**Parent Project**: See [amplifier documentation](../../README.md) for general setup
