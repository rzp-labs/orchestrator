#!/usr/bin/env python3
"""Log triage execution metadata for optimization analysis.

Claude Code hook that captures triage metrics for performance analysis
and workflow optimization. Reads result data from stdin and logs to both
human-readable logs and machine-parseable JSONL format.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

from hook_logger import HookLogger

logger = HookLogger("post_triage")


def main() -> None:
    """Process triage workflow result and log metrics."""
    try:
        # Read workflow result from stdin (Claude Code protocol)
        input_data = json.load(sys.stdin)

        # Extract key metrics
        ticket_id = input_data.get("ticket_id", "unknown")
        duration = input_data.get("duration", 0.0)
        success = input_data.get("success", False)
        agents_used = input_data.get("agents_used", [])

        # Log to human-readable format
        logger.info(f"Triage completed for ticket {ticket_id}")
        logger.info(f"Analysis duration: {duration}s")
        logger.info(f"Success: {success}")
        if agents_used:
            logger.info(f"Agents used: {', '.join(agents_used)}")

        # Create logs directory if needed
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # Log metrics to JSONL for future optimization
        metrics_file = logs_dir / "triage_metrics.jsonl"
        with open(metrics_file, "a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "ticket_id": ticket_id,
                        "duration": duration,
                        "agents_used": agents_used,
                        "success": success,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                + "\n"
            )

        # Return metadata (Claude Code protocol)
        json.dump({"metadata": {"logged": True}}, sys.stdout)

    except Exception as e:
        logger.error(f"Hook execution failed: {e}")
        # Return error metadata
        json.dump({"metadata": {"logged": False, "error": str(e)}}, sys.stdout)
        sys.exit(1)


if __name__ == "__main__":
    main()
