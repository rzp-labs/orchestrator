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

        click.echo(f"✓ Triage complete for {ticket_id} ({result.duration:.1f}s total)")
        click.echo("✓ Updated Linear ticket with AI analysis")
    else:
        click.echo(f"✗ Triage failed: {result.error}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
