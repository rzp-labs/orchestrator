# Adding Workflows

Guide for creating new workflows in Orchestrator.

## Overview

Workflows are Python modules that orchestrate external tools and AI agents to automate tactical product development tasks.

## Workflow Structure

Each workflow is a Python module with:
- Pydantic models for inputs/outputs
- Main workflow function
- Error handling
- Progress reporting

## Creating a Workflow

### Step 1: Define Models

Create Pydantic models in `src/orchestrator/models.py`:

```python
from pydantic import BaseModel

class MyWorkflowInput(BaseModel):
    """Input data for workflow"""
    param1: str
    param2: int | None = None

class MyWorkflowResult(BaseModel):
    """Output data from workflow"""
    success: bool
    outputs: dict
    errors: list[str] = []
```

### Step 2: Create Workflow Module

Create `src/orchestrator/my_workflow.py`:

```python
import asyncio
from .models import MyWorkflowInput, MyWorkflowResult
from .utils import retry_cli_command, run_agent, parse_llm_json

async def execute_my_workflow(input_data: MyWorkflowInput) -> MyWorkflowResult:
    \"\"\"Execute my workflow\"\"\"
    try:
        # Step 1: Fetch data from external tool
        data = await retry_cli_command(["some-cli", "get", input_data.param1])

        # Step 2: Delegate to AI agent
        analysis = await run_agent(
            agent_name="analysis-expert",
            task_description=f"Analyze this data: {data}"
        )

        # Step 3: Parse response
        result = parse_llm_json(analysis)

        # Step 4: Update external tool
        await retry_cli_command([
            "some-cli", "update",
            input_data.param1,
            "--data", result
        ])

        return MyWorkflowResult(
            success=True,
            outputs=result
        )
    except Exception as e:
        return MyWorkflowResult(
            success=False,
            outputs={},
            errors=[str(e)]
        )
```

### Step 3: Add CLI Command

Add command to `src/orchestrator/cli.py`:

```python
@click.command()
@click.argument("param1")
@click.option("--param2", type=int, help="Optional parameter")
def my_workflow(param1: str, param2: int | None = None):
    \"\"\"Execute my workflow\"\"\"
    input_data = MyWorkflowInput(param1=param1, param2=param2)
    result = asyncio.run(execute_my_workflow(input_data))

    if result.success:
        click.echo("✓ Workflow complete")
    else:
        click.echo(f"✗ Workflow failed: {result.errors}")
        sys.exit(1)

# Register command
cli.add_command(my_workflow)
```

### Step 4: Add Tests

Create `tests/test_my_workflow.py`:

```python
import pytest
from orchestrator.models import MyWorkflowInput
from orchestrator.my_workflow import execute_my_workflow

@pytest.mark.asyncio
async def test_my_workflow_success():
    \"\"\"Test successful workflow execution\"\"\"
    input_data = MyWorkflowInput(param1="test")
    result = await execute_my_workflow(input_data)

    assert result.success
    assert result.outputs
    assert not result.errors

@pytest.mark.asyncio
async def test_my_workflow_invalid_input():
    \"\"\"Test workflow with invalid input\"\"\"
    input_data = MyWorkflowInput(param1="")
    result = await execute_my_workflow(input_data)

    assert not result.success
    assert result.errors
```

### Step 5: Document

Add to `docs/workflows.md`:

```markdown
## My Workflow

Description of what this workflow does.

### Usage

\`\`\`bash
uv run orchestrator my-workflow <param1> [--param2 VALUE]
\`\`\`

### What It Does

1. Step 1 description
2. Step 2 description
3. Step 3 description
```

## Best Practices

### Use Defensive Utilities

Always use defensive patterns for LLM responses:

```python
# Good: Defensive parsing
result = parse_llm_json(llm_response)

# Bad: Direct JSON parsing
result = json.loads(llm_response)  # Will fail on markdown blocks
```

### Implement Retry Logic

Use retry for external CLI tools:

```python
# Good: Automatic retry
data = await retry_cli_command(["cli", "get", "id"])

# Bad: No retry
data = subprocess.run(["cli", "get", "id"])  # Fails on transient errors
```

### Progress Reporting

Provide progress feedback to users:

```python
click.echo("Fetching data...")
data = await fetch()
click.echo("✓ Data fetched")

click.echo("Analyzing...")
analysis = await analyze(data)
click.echo("✓ Analysis complete")
```

### Error Handling

Handle errors gracefully:

```python
try:
    result = await risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    return WorkflowResult(
        success=False,
        errors=[f"Operation failed: {e}"]
    )
```

## Testing Workflows

### Unit Tests

Test individual functions:

```bash
pytest tests/test_my_workflow.py::test_specific_function -v
```

### Integration Tests

Test with mocked CLI tools:

```python
@pytest.mark.asyncio
async def test_workflow_with_mocked_cli(mocker):
    mocker.patch("orchestrator.utils.retry_cli_command")
    result = await execute_my_workflow(input_data)
    assert result.success
```

### End-to-End Tests

Test with real external tools (manually):

```bash
uv run orchestrator my-workflow test-data
```

## Related Documentation

- **[Workflows](workflows.md)** - Existing workflows
- **[Architecture](architecture.md)** - Design patterns
- **[Hooks & Skills](hooks_and_skills.md)** - Automation
