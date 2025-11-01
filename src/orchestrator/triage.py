"""Main triage workflow orchestration.

This module implements the core support triage workflow that:
1. Fetches ticket from Linear (via GraphQL API)
2. Analyzes validity using analysis-expert agent
3. Assesses severity using bug-hunter agent
4. Updates Linear with AI analysis and priority

The workflow is fail-safe: errors return TriageResult with success=False
rather than raising exceptions, allowing for graceful error handling.
"""

import logging
import time

from orchestrator.config import get_linear_writes_enabled
from orchestrator.config import get_write_mode_display
from orchestrator.file_writer import save_analysis
from orchestrator.linear_client import fetch_issue
from orchestrator.linear_client import update_issue
from orchestrator.models import SeverityAnalysis
from orchestrator.models import TriageResult
from orchestrator.models import ValidityAnalysis
from orchestrator.utils import call_agent_with_retry

logger = logging.getLogger(__name__)


def severity_to_priority(severity: str) -> int:
    """Convert severity string to Linear priority level.

    Linear priorities: 0=none, 1=urgent, 2=high, 3=medium, 4=low

    Args:
        severity: Severity level (P0, P1, P2, P3)

    Returns:
        Priority level for Linear (0-4)
    """
    mapping = {
        "P0": 1,  # Urgent
        "P1": 2,  # High
        "P2": 3,  # Medium
        "P3": 4,  # Low
    }
    return mapping.get(severity, 0)


def execute_triage(ticket_id: str) -> TriageResult:
    """Execute support triage workflow.

    Steps (per docs/workflows.md lines 18-27):
    1. Fetch ticket from Linear
    2. Analyze validity (analysis-expert agent)
    3. Assess severity (bug-hunter agent)
    4. Update Linear with AI analysis

    Args:
        ticket_id: Linear ticket identifier (e.g., "ABC-123")

    Returns:
        TriageResult with all analysis data and execution metadata
    """
    start_time = time.time()

    try:
        # Show write mode
        mode_display = get_write_mode_display()
        writes_enabled = get_linear_writes_enabled()
        action_future = "WILL" if writes_enabled else "will NOT"
        logger.info(f"Mode: {mode_display} - Comments {action_future} be added to Linear")
        logger.info(f"Beginning analysis for Linear issue {ticket_id}...")

        # Step 1: Fetch ticket (docs/workflows.md lines 82-94)
        logger.info(f"Fetching ticket {ticket_id}")
        ticket_data = fetch_issue(ticket_id)

        # Step 2: Validity analysis (docs/workflows.md lines 96-120)
        logger.info("Analyzing validity")
        validity = call_agent_with_retry(
            agent_name="analysis-expert",
            task="Analyze ticket validity",
            data={"ticket": ticket_data},
            schema=ValidityAnalysis,
        )

        # Step 3: Severity assessment (docs/workflows.md lines 122-148)
        logger.info("Assessing severity")
        severity = call_agent_with_retry(
            agent_name="bug-hunter",
            task="Assess severity and priority",
            data={"ticket": ticket_data},
            schema=SeverityAnalysis,
        )

        # Step 4: Format AI comment
        logger.info("Formatting AI comment")
        comment = format_ai_comment(validity, severity)

        # Save analysis to file (always)
        file_path = save_analysis(
            ticket_id=ticket_id,
            comment=comment,
            writes_enabled=writes_enabled,
        )
        logger.info(f"✓ Saved to: {file_path}")

        # Update Linear if writes enabled
        priority_level = severity_to_priority(severity.severity)
        update_issue(ticket_id, priority_level, comment)

        duration = time.time() - start_time
        logger.info(f"✓ Triage complete for {ticket_id} ({duration:.1f}s total)")

        # Confirm what happened with Linear
        if writes_enabled:
            logger.info(f"✓ Posted comment to Linear issue {ticket_id}")
        else:
            logger.info("ℹ Linear writes disabled (LINEAR_ENABLE_WRITES=false)")

        return TriageResult(
            ticket_id=ticket_id,
            ticket_url=f"https://linear.app/issue/{ticket_id}",
            validity=validity,
            severity=severity,
            ai_comment=comment,
            success=True,
            duration=duration,
            agents_used=["analysis-expert", "bug-hunter"],
        )

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Triage failed: {e}")
        # Return failure result instead of raising
        return TriageResult(
            ticket_id=ticket_id,
            ticket_url=f"https://linear.app/issue/{ticket_id}",
            validity=None,
            severity=None,
            ai_comment="",
            success=False,
            duration=duration,
            agents_used=[],
            error=str(e),
        )


def format_ai_comment(validity: ValidityAnalysis, severity: SeverityAnalysis) -> str:
    """Format AI analysis as Linear comment.

    Format per docs/workflows.md lines 162-178

    Args:
        validity: Validity analysis result
        severity: Severity assessment result

    Returns:
        Formatted markdown comment for Linear
    """
    missing_context_section = ""
    if validity.missing_context:
        items = "\n".join(f"- {item}" for item in validity.missing_context)
        missing_context_section = f"\n#### Missing Context\n{items}\n"

    return f"""## AI Triage Analysis

**Validity**: {"Valid" if validity.is_valid else "Invalid"}, {"Actionable" if validity.is_actionable else "Not Actionable"}
**Severity**: {severity.severity}
**Complexity**: {severity.complexity.capitalize()}
**Required Expertise**: {", ".join(severity.required_expertise) if severity.required_expertise else "None"}

### Validity Analysis
{validity.reasoning}
{missing_context_section}
### Severity Assessment
{severity.reasoning}

---
*Generated by Orchestrator*
"""
