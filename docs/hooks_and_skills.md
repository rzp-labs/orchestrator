# Hooks & Skills

Claude Code integration patterns in Orchestrator.

## Overview

Orchestrator uses Claude Code hooks for logging and metrics collection, following the amplifier pattern exactly.

**Key principle**: Python does orchestration, hooks do logging.

## Hooks Pattern

### How Amplifier Uses Hooks

Hooks are Python scripts that:
1. Read JSON from stdin
2. Call Python modules for actual logic
3. Log outcomes to files
4. Write JSON to stdout (Claude Code protocol)

**Example from amplifier**:
```python
#!/usr/bin/env python3
from hook_logger import HookLogger

logger = HookLogger("hook_name")

def main():
    input_data = json.load(sys.stdin)
    logger.info("Processing...")

    # Actual logic via modules
    result = process(input_data)

    logger.info(f"Complete: {result}")
    json.dump({"metadata": {...}}, sys.stdout)
```

### Orchestrator Hook Implementation

**hook_post_triage.py** - Logs metrics after triage workflow:

```python
#!/usr/bin/env python3
\"\"\"Log triage execution metadata for optimization analysis\"\"\"

from hook_logger import HookLogger
import json, sys

logger = HookLogger("post_triage")

def main():
    # Read workflow result from stdin
    input_data = json.load(sys.stdin)

    logger.info(f"Triage completed for ticket {input_data.get('ticket_id')}")

    # Log metrics for future optimization
    with open("logs/triage_metrics.jsonl", "a") as f:
        f.write(json.dumps({
            "ticket_id": input_data.get("ticket_id"),
            "duration": input_data.get("duration"),
            "success": input_data.get("success")
        }) + "\\n")

    # Return metadata (Claude Code protocol)
    json.dump({"metadata": {"logged": True}}, sys.stdout)

if __name__ == "__main__":
    main()
```

## Hook Logger

**hook_logger.py** - Shared logging utility:

```python
class HookLogger:
    \"\"\"File-based logging for hooks\"\"\"

    def __init__(self, hook_name: str):
        self.hook_name = hook_name
        self.log_file = f"logs/{hook_name}_{date}.log"

    def info(self, message: str):
        \"\"\"Log info level message\"\"\"
        self._write(f"[INFO] {message}")

    def error(self, message: str):
        \"\"\"Log error level message\"\"\"
        self._write(f"[ERROR] {message}")

    def _write(self, message: str):
        \"\"\"Write to log file\"\"\"
        timestamp = datetime.now().isoformat()
        with open(self.log_file, "a") as f:
            f.write(f"[{timestamp}] {message}\\n")
```

## What Hooks Are For

**Use hooks for**:
- Logging execution metadata
- Collecting metrics for optimization
- Cleanup tasks after workflows
- Notification of completion

**NOT for**:
- Orchestrating workflows (Python does this)
- Complex business logic (belongs in modules)
- Decision making (happens in workflows)
- Event detection (manual invocation for now)

## Metrics Collection

Hooks log metrics to JSONL files for analysis:

**triage_metrics.jsonl**:
```json
{"ticket_id": "ABC-123", "duration": 23.5, "success": true}
{"ticket_id": "ABC-124", "duration": 18.2, "success": true}
{"ticket_id": "ABC-125", "duration": 45.1, "success": false}
```

Metrics used for:
- Performance monitoring
- Success rate tracking
- Identifying slow workflows
- Optimization opportunities

## Viewing Logs

**Tail hook logs**:
```bash
tail -f logs/post_triage_*.log
```

**Search for errors**:
```bash
grep ERROR logs/*.log
```

**Analyze metrics**:
```bash
# Average duration
jq -s 'map(.duration) | add/length' logs/triage_metrics.jsonl

# Success rate
jq -s 'map(.success) | map(select(. == true)) | length' logs/triage_metrics.jsonl
```

## Adding New Hooks

### Step 1: Create Hook Script

Create `.claude/tools/hook_<name>.py`:

```python
#!/usr/bin/env python3
from hook_logger import HookLogger
import json, sys

logger = HookLogger("my_hook")

def main():
    input_data = json.load(sys.stdin)

    logger.info("Hook executing...")

    # Your logic here

    json.dump({"metadata": {"status": "complete"}}, sys.stdout)

if __name__ == "__main__":
    main()
```

### Step 2: Make Executable

```bash
chmod +x .claude/tools/hook_<name>.py
```

### Step 3: Test Hook

```bash
# Test with sample input
echo '{"test": "data"}' | .claude/tools/hook_<name>.py
```

## Comparison: Hooks vs Workflows

| Aspect | Workflows | Hooks |
|--------|-----------|-------|
| **Purpose** | Orchestrate tasks | Log outcomes |
| **Invocation** | Manual (CLI) | After workflow |
| **Logic** | Business logic | Logging/metrics |
| **Language** | Python modules | Python scripts |
| **Input** | CLI arguments | Workflow result (stdin) |
| **Output** | User feedback | Metrics files |
| **Duration** | 20-30 seconds | <1 second |

## Related Documentation

- **[Architecture](architecture.md)** - Design patterns
- **[Workflows](workflows.md)** - Workflow implementation
- **[Adding Workflows](adding_workflows.md)** - Creating workflows
