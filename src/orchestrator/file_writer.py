"""File writer for saving triage analysis results.

This module saves triage analysis to markdown files in ./triage_results/,
providing durable storage of expensive LLM analyses.
"""

import logging
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def save_analysis(
    ticket_id: str,
    comment: str,
    writes_enabled: bool,
    output_dir: Path = Path("./triage_results"),
) -> Path:
    """Save triage analysis to markdown file.

    Args:
        ticket_id: Linear ticket ID (e.g., "SP-1242")
        comment: Formatted AI analysis comment (markdown)
        writes_enabled: Whether Linear writes are enabled
        output_dir: Directory to save results (default: ./triage_results)

    Returns:
        Path: Path to saved file

    Raises:
        OSError: If directory can't be created or file can't be written
    """
    # Create directory if needed
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate file path
    file_path = output_dir / f"{ticket_id}.md"

    # Add metadata footer
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    mode = "enabled" if writes_enabled else "disabled"

    content = f"""{comment}

---
_Analysis generated: {timestamp}_
_Linear writes: {mode}_
"""

    # Write file
    file_path.write_text(content, encoding="utf-8")
    logger.info(f"Saved analysis to {file_path}")

    return file_path
