#!/usr/bin/env python3
"""Log investigation execution metadata for optimization analysis.

Claude Code hook that captures investigation metrics for performance analysis
and pattern learning effectiveness. Reads result data from stdin and logs to both
human-readable logs and machine-parseable JSONL format.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

from hook_logger import HookLogger

logger = HookLogger("post_investigation")


def main() -> None:
    """Process investigation workflow result and log metrics."""
    try:
        # Read workflow result from stdin (Claude Code protocol)
        input_data = json.load(sys.stdin)

        # Extract key metrics
        issue_id = input_data.get("issue_id", "unknown")
        duration = input_data.get("duration", 0.0)
        success = input_data.get("success", False)
        agents_used = input_data.get("agents_used", [])
        similar_issues_count = input_data.get("similar_issues_count", 0)
        findings_count = len(input_data.get("findings", []))
        recommendations_count = len(input_data.get("recommendations", []))
        pattern_matches = len(input_data.get("pattern_matches", []))
        citations_count = input_data.get("citations_count", 0)

        # Log to human-readable format
        logger.info(f"Investigation completed for issue {issue_id}")
        logger.info(f"Investigation duration: {duration}s")
        logger.info(f"Success: {success}")
        logger.info(f"Similar issues found: {similar_issues_count}")
        logger.info(f"Findings generated: {findings_count}")
        logger.info(f"Recommendations generated: {recommendations_count}")
        logger.info(f"Pattern matches: {pattern_matches}")
        logger.info(f"Citations provided: {citations_count}")
        if agents_used:
            logger.info(f"Agents used: {', '.join(agents_used)}")

        # Create logs directory if needed
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # Log metrics to JSONL for future optimization
        metrics_file = logs_dir / "investigation_metrics.jsonl"
        with open(metrics_file, "a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "issue_id": issue_id,
                        "duration": duration,
                        "agents_used": agents_used,
                        "similar_issues_count": similar_issues_count,
                        "findings_count": findings_count,
                        "recommendations_count": recommendations_count,
                        "pattern_matches": pattern_matches,
                        "citations_count": citations_count,
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
