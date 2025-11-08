"""Citation tracking and formatting for investigation workflow."""

from orchestrator.models import Citation, Finding, Recommendation


class CitationTracker:
    """Tracks and formats citations for investigation findings and recommendations."""

    def __init__(self) -> None:
        """Initialize citation tracker with empty citation store."""
        self.citations: list[Citation] = []

    def add_citation(self, citation: Citation) -> None:
        """Add a citation to the tracker.

        Args:
            citation: Citation to add to the store
        """
        self.citations.append(citation)

    def validate_finding(self, finding: Finding) -> tuple[bool, str]:
        """Validate that a finding has at least one citation.

        Args:
            finding: Finding to validate

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if finding has ≥1 citation
            - error_message: Description of validation failure (empty if valid)
        """
        if len(finding.citations) < 1:
            truncated = finding.finding[:50]
            suffix = "..." if len(finding.finding) > 50 else ""
            return False, f"Finding '{truncated}{suffix}' has no citations (required: ≥1)"
        return True, ""

    def validate_recommendation(self, recommendation: Recommendation) -> tuple[bool, str]:
        """Validate that a recommendation has at least one citation.

        Args:
            recommendation: Recommendation to validate

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if recommendation has ≥1 citation
            - error_message: Description of validation failure (empty if valid)
        """
        if len(recommendation.citations) < 1:
            truncated = recommendation.recommendation[:50]
            suffix = "..." if len(recommendation.recommendation) > 50 else ""
            return False, f"Recommendation '{truncated}{suffix}' has no citations (required: ≥1)"
        return True, ""

    def format_citation(self, citation: Citation) -> str:
        """Format a single citation as markdown with direct link.

        Args:
            citation: Citation to format

        Returns:
            Markdown-formatted citation string with link
        """
        return f'- [{citation.source_type}: {citation.source_id}]({citation.source_url}): "{citation.excerpt}"'

    def format_citations_list(self, citations: list[Citation]) -> str:
        """Format a list of citations as markdown.

        Args:
            citations: List of citations to format

        Returns:
            Multi-line markdown string with all citations
        """
        if not citations:
            return "(No citations)"

        lines = ["**Supporting Evidence:**"]
        for citation in citations:
            lines.append(self.format_citation(citation))
        return "\n".join(lines)

    def get_total_citations(self) -> int:
        """Get total number of citations collected.

        Returns:
            Count of citations in the tracker
        """
        return len(self.citations)
