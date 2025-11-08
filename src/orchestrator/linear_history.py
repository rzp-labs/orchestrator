"""Linear issue history research for investigation workflow."""

from typing import Any

from orchestrator.linear_client import fetch_issue
from orchestrator.models import Citation


class LinearHistoryResearcher:
    """Research Linear issue history to find patterns and similar issues."""

    def __init__(self) -> None:
        """Initialize Linear history researcher."""
        # No initialization needed - all methods are stateless
        # and use linear_client functions directly

    def find_similar_issues(self, issue_id: str, max_results: int = 50) -> list[dict[str, Any]]:
        """Find similar issues in Linear by labels, components, and text patterns.

        Args:
            issue_id: Current issue ID to find similar issues for
            max_results: Maximum number of similar issues to return (default: 50)

        Returns:
            List of dictionaries with similar issue data:
            - id: Issue identifier
            - url: Issue URL
            - title: Issue title
            - description: Issue description (first 200 chars)
            - state: Issue state (e.g., "completed", "in_progress")
            - labels: Comma-separated label names
        """
        # Fetch current issue to get labels/components for matching
        current_issue = fetch_issue(issue_id)

        # For now, return empty list - will be enhanced with GraphQL queries
        # This is a simplified implementation
        # Real implementation would use fetch_similar_issues from linear_client
        # when that function is implemented

        # Placeholder implementation - will query GraphQL in future
        # similar = fetch_similar_issues(
        #     issue_id=issue_id,
        #     labels=current_issue.get("labels", []),
        #     max_results=max_results
        # )

        results: list[dict[str, Any]] = []

        # For now, just return the current issue as a template
        # Real implementation will query Linear for similar issues
        if current_issue:
            results.append(
                {
                    "id": issue_id,
                    "url": f"https://linear.app/issue/{issue_id}",
                    "title": current_issue.get("title", "")[:200],
                    "description": current_issue.get("description", "")[:200],
                    "state": current_issue.get("state", {}).get("name", "unknown"),
                    "labels": "",  # Will be populated when GraphQL includes labels
                }
            )

        return results[:max_results]

    def extract_citations_from_issue(self, issue: dict[str, Any]) -> Citation:
        """Create a Citation object from a similar issue.

        Args:
            issue: Issue dictionary from find_similar_issues()

        Returns:
            Citation object for this issue
        """
        # Extract meaningful excerpt from title + description
        excerpt = f"{issue['title']}"
        if issue.get("description"):
            # Add first sentence of description if available
            desc = issue["description"].split(".")[0]
            if len(desc) > 0 and len(desc) < 150:
                excerpt += f": {desc}"

        return Citation(
            source_type="linear_issue",
            source_id=issue["id"],
            source_url=issue["url"],
            excerpt=excerpt[:200],  # Truncate to 200 chars for readability
        )

    def find_resolution_patterns(self, similar_issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Identify common resolution patterns from similar issues.

        Args:
            similar_issues: List of similar issues from find_similar_issues()

        Returns:
            List of pattern dictionaries:
            - pattern: Description of the pattern
            - count: Number of times this pattern occurred
            - example_issue_id: Example issue ID showing this pattern
        """
        patterns: dict[str, dict[str, Any]] = {}

        # Group by state to identify resolution patterns
        for issue in similar_issues:
            state = issue["state"]

            # Count completed/resolved issues
            if state in ("completed", "done", "closed"):
                pattern_key = f"Resolved with state: {state}"
                if pattern_key not in patterns:
                    patterns[pattern_key] = {
                        "pattern": pattern_key,
                        "count": 0,
                        "example_issue_id": issue["id"],
                    }
                patterns[pattern_key]["count"] = int(patterns[pattern_key]["count"]) + 1

        # Convert to list and sort by count descending
        result = list(patterns.values())
        result.sort(key=lambda p: int(p["count"]), reverse=True)
        return result

    def find_team_expertise(self, similar_issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Identify team members with expertise in similar issues.

        Args:
            similar_issues: List of similar issues from find_similar_issues()

        Returns:
            List of expertise dictionaries:
            - team_member: Team member identifier
            - resolved_count: Number of similar issues they resolved
            - example_issue_id: Example issue they resolved
        """
        # Note: This is a simplified implementation
        # Real implementation would fetch assignee data from Linear API

        # For now, return empty list since we don't have assignee data
        # in the basic similar_issues structure
        # This can be enhanced later when GraphQL query includes assignee field

        return []
