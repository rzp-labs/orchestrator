"""Click CLI interface for orchestrator.

Provides command-line interface for running triage workflows and other
orchestration tasks.
"""

import sys

import click

from orchestrator.triage import execute_triage


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """Orchestrator - AI-powered tactical product development automation."""
    pass


@cli.command()
@click.argument("ticket_id")
def triage(ticket_id: str) -> None:
    """Analyze Linear support ticket.

    Usage: orchestrator triage ABC-123

    Specification: docs/workflows.md lines 29-40
    """
    from pathlib import Path

    from orchestrator.config import get_linear_writes_enabled, get_write_mode_display

    # Show write mode
    mode_display = get_write_mode_display()
    writes_enabled = get_linear_writes_enabled()
    action_future = "WILL" if writes_enabled else "will NOT"
    click.echo(f"Mode: {mode_display} - Comments {action_future} be added to Linear")
    click.echo(f"Beginning analysis for Linear issue {ticket_id}...")
    click.echo("")

    click.echo(f"Fetching ticket {ticket_id}...")

    result = execute_triage(ticket_id)

    if result.success:
        click.echo(f"✓ Ticket fetched: {result.ticket_url}")
        click.echo("")

        # Validity analysis output
        click.echo("Analyzing validity...")
        click.echo("✓ Validity analysis complete")
        if result.validity:
            click.echo(f"  - Valid: {result.validity.is_valid}")
            click.echo(f"  - Actionable: {result.validity.is_actionable}")
            if result.validity.missing_context:
                click.echo(f"  - Missing context: {', '.join(result.validity.missing_context)}")
        click.echo("")

        # Severity assessment output
        click.echo("Assessing severity...")
        click.echo("✓ Severity assessment complete")
        if result.severity:
            click.echo(f"  - Priority: {result.severity.severity}")
            click.echo(f"  - Complexity: {result.severity.complexity}")
            if result.severity.required_expertise:
                click.echo(f"  - Required expertise: {', '.join(result.severity.required_expertise)}")
        click.echo("")

        # Show file save location
        file_path = Path(f"./triage_results/{ticket_id}.md")
        click.echo(f"✓ Saved to: {file_path}")
        click.echo("")

        click.echo(f"✓ Triage complete for {ticket_id} ({result.duration:.1f}s total)")

        # Confirm what happened with Linear
        if writes_enabled:
            click.echo(f"✓ Posted comment to Linear issue {ticket_id}")
        else:
            click.echo("ℹ Linear writes disabled (LINEAR_ENABLE_WRITES=false)")
    else:
        click.echo(f"✗ Triage failed: {result.error}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("issue_id")
def investigate(issue_id: str) -> None:
    """Research Linear issue history and provide evidence-based recommendations.

    Usage: orchestrator investigate ABC-456

    Specification: docs/workflows.md lines 200-250
    """
    from pathlib import Path

    from orchestrator.investigation import execute_investigation

    click.echo(f"Beginning investigation for Linear issue {issue_id}...")
    click.echo("")

    click.echo(f"Fetching issue {issue_id}...")

    result = execute_investigation(issue_id)

    if result.success:
        click.echo(f"✓ Issue fetched: {result.issue_url}")
        click.echo("")

        click.echo(f"Researching Linear history... (found {result.similar_issues_count} similar issues)")
        click.echo("✓ Research complete")
        click.echo("")

        click.echo(f"Synthesizing findings... ({len(result.findings)} findings)")
        click.echo("✓ Synthesis complete")
        click.echo("")

        click.echo(f"Generating recommendations... ({len(result.recommendations)} recommendations)")
        click.echo("✓ Recommendations generated")
        click.echo("")

        # Show file save location
        file_path = Path(f"./investigation_results/{issue_id}.md")
        click.echo(f"✓ Saved to: {file_path}")
        click.echo("")

        click.echo(f"✓ Investigation complete for {issue_id} ({result.duration:.1f}s total)")
        click.echo(f"  - Findings: {len(result.findings)}")
        click.echo(f"  - Recommendations: {len(result.recommendations)}")
        click.echo(f"  - Pattern matches: {len(result.pattern_matches)}")
        click.echo(f"  - Citations: {result.citations_count}")
    else:
        click.echo(f"✗ Investigation failed: {result.error}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
