"""Linear GraphQL API client.

This module provides direct GraphQL API access to Linear, replacing CLI-based interaction.
It implements the minimal set of operations needed for triage workflow.
"""

import logging
import os
from typing import Any

import requests

from orchestrator.config import get_linear_writes_enabled

logger = logging.getLogger(__name__)

LINEAR_API_ENDPOINT = "https://api.linear.app/graphql"


def _get_api_key() -> str:
    """Get Linear API key from environment.

    Returns:
        LINEAR_API_KEY from environment

    Raises:
        RuntimeError: If LINEAR_API_KEY not set
    """
    api_key = os.environ.get("LINEAR_API_KEY")
    if not api_key:
        raise RuntimeError(
            "LINEAR_API_KEY environment variable not set. Get your API key from https://linear.app/settings/api"
        )
    return api_key


def _make_graphql_request(query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    """Make GraphQL request to Linear API.

    Args:
        query: GraphQL query or mutation string
        variables: Optional variables for the query

    Returns:
        Response data from GraphQL API

    Raises:
        RuntimeError: If request fails or returns errors
    """
    api_key = _get_api_key()

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
    }

    payload: dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables

    try:
        response = requests.post(LINEAR_API_ENDPOINT, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Linear API request failed: {e}") from e

    data = response.json()

    # Check for GraphQL errors
    if "errors" in data:
        error_messages = [err.get("message", str(err)) for err in data["errors"]]
        raise RuntimeError(f"Linear API returned errors: {', '.join(error_messages)}")

    return data.get("data", {})


def fetch_issue(issue_id: str) -> dict[str, Any]:
    """Fetch issue from Linear GraphQL API.

    Args:
        issue_id: Linear issue ID (e.g., "SP-1242")

    Returns:
        {
            "id": str,
            "title": str,
            "description": str,
            "priority": int,  # 0-4
            "state": {"name": str},
            "team": {"key": str},
        }

    Raises:
        RuntimeError: If API request fails or issue not found
    """
    query = """
    query GetIssue($id: String!) {
        issue(id: $id) {
            id
            title
            description
            priority
            state {
                name
            }
            team {
                key
            }
        }
    }
    """

    logger.info(f"Fetching issue {issue_id} from Linear API")

    data = _make_graphql_request(query, {"id": issue_id})

    if not data.get("issue"):
        raise RuntimeError(f"Issue {issue_id} not found")

    return data["issue"]


def update_issue(issue_id: str, priority: int, comment: str) -> None:
    """Update issue priority and add comment.

    If LINEAR_ENABLE_WRITES is disabled, logs what would have been
    written but does not make API calls.

    Args:
        issue_id: Linear issue ID
        priority: Priority level (0=none, 1=urgent, 2=high, 3=medium, 4=low)
        comment: Markdown comment to add

    Raises:
        RuntimeError: If update fails (only when writes enabled)
    """
    if not get_linear_writes_enabled():
        logger.info(
            f"[READ-ONLY] Skipping Linear update for {issue_id} (priority={priority}, comment={len(comment)} chars)"
        )
        return

    # First, update priority
    update_mutation = """
    mutation UpdateIssuePriority($id: String!, $priority: Int!) {
        issueUpdate(id: $id, input: { priority: $priority }) {
            success
            issue {
                id
                priority
            }
        }
    }
    """

    logger.info(f"Updating issue {issue_id} priority to {priority}")

    update_data = _make_graphql_request(update_mutation, {"id": issue_id, "priority": priority})

    if not update_data.get("issueUpdate", {}).get("success"):
        raise RuntimeError(f"Failed to update issue {issue_id} priority")

    # Then, add comment
    comment_mutation = """
    mutation AddComment($issueId: String!, $body: String!) {
        commentCreate(input: { issueId: $issueId, body: $body }) {
            success
            comment {
                id
            }
        }
    }
    """

    logger.info(f"Adding comment to issue {issue_id}")

    comment_data = _make_graphql_request(comment_mutation, {"issueId": issue_id, "body": comment})

    if not comment_data.get("commentCreate", {}).get("success"):
        raise RuntimeError(f"Failed to add comment to issue {issue_id}")

    logger.info(f"Successfully updated issue {issue_id}")
