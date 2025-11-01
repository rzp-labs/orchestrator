"""Tests for Linear GraphQL API client."""

import os
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import requests

from orchestrator.linear_client import fetch_issue
from orchestrator.linear_client import update_issue


class TestFetchIssue:
    """Test fetch_issue() function."""

    @patch("orchestrator.linear_client.requests.post")
    @patch.dict(os.environ, {"LINEAR_API_KEY": "test_api_key"})
    def test_fetch_issue_success(self, mock_post):
        """Test successful issue fetch from Linear API."""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "issue": {
                    "id": "SP-1242",
                    "title": "Test bug",
                    "description": "Bug description",
                    "priority": 2,
                    "state": {"name": "In Progress"},
                    "team": {"key": "SP"},
                }
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        result = fetch_issue("SP-1242")

        assert result["id"] == "SP-1242"
        assert result["title"] == "Test bug"
        assert result["priority"] == 2
        assert result["state"]["name"] == "In Progress"

        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args.kwargs["headers"]["Authorization"] == "test_api_key"
        assert "issue(id:" in call_args.kwargs["json"]["query"]

    @patch("orchestrator.linear_client.requests.post")
    @patch.dict(os.environ, {"LINEAR_API_KEY": "test_api_key"})
    def test_fetch_issue_not_found(self, mock_post):
        """Test error handling when issue not found."""
        # Mock API response with no issue
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"issue": None}}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with pytest.raises(RuntimeError, match="Issue SP-999 not found"):
            fetch_issue("SP-999")

    @patch("orchestrator.linear_client.requests.post")
    @patch.dict(os.environ, {"LINEAR_API_KEY": "test_api_key"})
    def test_fetch_issue_api_error(self, mock_post):
        """Test error handling when API returns GraphQL errors."""
        # Mock API response with errors
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "errors": [{"message": "Invalid issue ID"}],
            "data": None,
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with pytest.raises(RuntimeError, match="Linear API returned errors"):
            fetch_issue("INVALID")

    @patch("orchestrator.linear_client.requests.post")
    @patch.dict(os.environ, {"LINEAR_API_KEY": "test_api_key"})
    def test_fetch_issue_network_error(self, mock_post):
        """Test error handling for network failures."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Network error")

        with pytest.raises(RuntimeError, match="Linear API request failed"):
            fetch_issue("SP-1242")

    @patch.dict(os.environ, {}, clear=True)
    def test_fetch_issue_missing_api_key(self):
        """Test error when LINEAR_API_KEY not set."""
        with pytest.raises(RuntimeError, match="LINEAR_API_KEY environment variable not set"):
            fetch_issue("SP-1242")


class TestUpdateIssue:
    """Test update_issue() function."""

    @patch("orchestrator.linear_client.requests.post")
    @patch.dict(os.environ, {"LINEAR_API_KEY": "test_api_key"})
    def test_update_issue_success(self, mock_post):
        """Test successful issue update and comment creation."""
        # Mock both mutations (priority update and comment creation)
        update_response = MagicMock()
        update_response.json.return_value = {
            "data": {
                "issueUpdate": {
                    "success": True,
                    "issue": {"id": "SP-1242", "priority": 2},
                }
            }
        }
        update_response.raise_for_status = MagicMock()

        comment_response = MagicMock()
        comment_response.json.return_value = {
            "data": {
                "commentCreate": {
                    "success": True,
                    "comment": {"id": "comment-123"},
                }
            }
        }
        comment_response.raise_for_status = MagicMock()

        mock_post.side_effect = [update_response, comment_response]

        update_issue("SP-1242", 2, "AI analysis comment")

        # Verify both API calls were made
        assert mock_post.call_count == 2

        # Verify priority update call
        first_call = mock_post.call_args_list[0]
        assert "issueUpdate" in first_call.kwargs["json"]["query"]
        assert first_call.kwargs["json"]["variables"]["priority"] == 2

        # Verify comment creation call
        second_call = mock_post.call_args_list[1]
        assert "commentCreate" in second_call.kwargs["json"]["query"]
        assert second_call.kwargs["json"]["variables"]["body"] == "AI analysis comment"

    @patch("orchestrator.linear_client.requests.post")
    @patch.dict(os.environ, {"LINEAR_API_KEY": "test_api_key"})
    def test_update_issue_priority_failure(self, mock_post):
        """Test error handling when priority update fails."""
        # Mock failed priority update
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": {
                "issueUpdate": {
                    "success": False,
                }
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        with pytest.raises(RuntimeError, match="Failed to update issue SP-1242 priority"):
            update_issue("SP-1242", 2, "Comment")

    @patch("orchestrator.linear_client.requests.post")
    @patch.dict(os.environ, {"LINEAR_API_KEY": "test_api_key"})
    def test_update_issue_comment_failure(self, mock_post):
        """Test error handling when comment creation fails."""
        # Mock successful priority update but failed comment
        update_response = MagicMock()
        update_response.json.return_value = {
            "data": {
                "issueUpdate": {
                    "success": True,
                    "issue": {"id": "SP-1242", "priority": 2},
                }
            }
        }
        update_response.raise_for_status = MagicMock()

        comment_response = MagicMock()
        comment_response.json.return_value = {
            "data": {
                "commentCreate": {
                    "success": False,
                }
            }
        }
        comment_response.raise_for_status = MagicMock()

        mock_post.side_effect = [update_response, comment_response]

        with pytest.raises(RuntimeError, match="Failed to add comment to issue SP-1242"):
            update_issue("SP-1242", 2, "Comment")

    @patch("orchestrator.linear_client.requests.post")
    @patch.dict(os.environ, {"LINEAR_API_KEY": "test_api_key"})
    def test_update_issue_network_error(self, mock_post):
        """Test error handling for network failures during update."""
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")

        with pytest.raises(RuntimeError, match="Linear API request failed"):
            update_issue("SP-1242", 2, "Comment")

    @patch("orchestrator.linear_client._make_graphql_request")
    @patch.dict(os.environ, {"LINEAR_API_KEY": "test_api_key"})
    def test_update_issue_respects_write_control(self, mock_request, disable_linear_writes):
        """update_issue skips API call when writes disabled."""
        # Mock would fail if called, proving it's not called
        update_issue("SP-123", priority=2, comment="test")
        mock_request.assert_not_called()

    @patch("orchestrator.linear_client._make_graphql_request")
    @patch.dict(os.environ, {"LINEAR_API_KEY": "test_api_key"})
    def test_update_issue_makes_call_when_enabled(self, mock_request, enable_linear_writes):
        """update_issue calls API when writes enabled."""
        mock_request.return_value = {
            "issueUpdate": {"success": True, "issue": {"id": "SP-123", "priority": 2}},
            "commentCreate": {"success": True, "comment": {"id": "comment-123"}},
        }
        # Call function twice for both mutations
        mock_request.side_effect = [
            {"issueUpdate": {"success": True, "issue": {"id": "SP-123", "priority": 2}}},
            {"commentCreate": {"success": True, "comment": {"id": "comment-123"}}},
        ]
        update_issue("SP-123", priority=2, comment="test")
        assert mock_request.call_count == 2  # priority + comment
