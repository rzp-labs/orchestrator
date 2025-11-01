"""Tests for triage workflow orchestration."""

import subprocess
from unittest.mock import patch

from orchestrator.models import SeverityAnalysis
from orchestrator.models import ValidityAnalysis
from orchestrator.triage import execute_triage
from orchestrator.triage import format_ai_comment
from orchestrator.triage import severity_to_priority


class TestExecuteTriage:
    """Test execute_triage() function."""

    @patch("orchestrator.triage.update_issue")
    @patch("orchestrator.triage.save_analysis")
    @patch("orchestrator.triage.fetch_issue")
    @patch("orchestrator.triage.call_agent_with_retry")
    def test_successful_triage(self, mock_agent_retry, mock_fetch, mock_save, mock_update):
        """Test complete successful triage workflow."""
        # Mock Linear ticket fetch
        mock_fetch.return_value = {"id": "ABC-123", "title": "Test bug"}

        # Mock agent responses (call_agent_with_retry returns Pydantic models directly)
        mock_agent_retry.side_effect = [
            ValidityAnalysis(
                is_valid=True,
                is_actionable=True,
                missing_context=[],
                reasoning="Valid bug report",
            ),
            SeverityAnalysis(
                severity="P1",
                complexity="medium",
                required_expertise=["Backend"],
                reasoning="Critical issue",
            ),
        ]

        result = execute_triage("ABC-123")

        assert result.success is True
        assert result.ticket_id == "ABC-123"
        assert result.validity is not None
        assert result.validity.is_valid is True
        assert result.severity is not None
        assert result.severity.severity == "P1"
        assert result.agents_used == ["analysis-expert", "bug-hunter"]
        assert result.error is None

    @patch("orchestrator.triage.update_issue")
    @patch("orchestrator.triage.save_analysis")
    @patch("orchestrator.triage.fetch_issue")
    @patch("orchestrator.triage.call_agent_with_retry")
    def test_triage_with_missing_context(self, mock_agent_retry, mock_fetch, mock_save, mock_update):
        """Test triage with validity requiring missing context."""
        # Mock Linear operations
        mock_fetch.return_value = {"id": "ABC-456", "title": "Incomplete report"}

        # Mock agent responses
        mock_agent_retry.side_effect = [
            ValidityAnalysis(
                is_valid=True,
                is_actionable=False,
                missing_context=["Reproduction steps", "Error logs"],
                reasoning="Need more information",
            ),
            SeverityAnalysis(
                severity="P3",
                complexity="simple",
                required_expertise=[],
                reasoning="Low priority",
            ),
        ]

        result = execute_triage("ABC-456")

        assert result.success is True
        assert result.validity is not None
        assert result.validity.is_actionable is False
        assert len(result.validity.missing_context) == 2
        assert "Reproduction steps" in result.validity.missing_context

    @patch("orchestrator.triage.fetch_issue")
    def test_triage_fails_on_ticket_fetch_error(self, mock_fetch):
        """Test that triage handles Linear fetch errors gracefully."""
        mock_fetch.side_effect = RuntimeError("Issue INVALID-999 not found")

        result = execute_triage("INVALID-999")

        assert result.success is False
        assert result.error is not None
        assert "not found" in result.error
        assert result.validity is None
        assert result.severity is None

    @patch("orchestrator.triage.fetch_issue")
    @patch("orchestrator.triage.call_agent_with_retry")
    def test_triage_fails_on_agent_error(self, mock_agent_retry, mock_fetch):
        """Test that triage handles agent execution errors gracefully."""
        # Mock successful ticket fetch
        mock_fetch.return_value = {"id": "ABC-789", "title": "Test"}

        # Mock agent failure
        mock_agent_retry.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["claude"], stderr="Agent failed"
        )

        result = execute_triage("ABC-789")

        assert result.success is False
        assert result.error is not None
        assert result.validity is None
        assert result.severity is None

    @patch("orchestrator.triage.fetch_issue")
    @patch("orchestrator.triage.call_agent_with_retry")
    def test_triage_fails_on_invalid_json(self, mock_agent_retry, mock_fetch):
        """Test that triage handles invalid LLM JSON gracefully."""
        # Mock successful ticket fetch
        mock_fetch.return_value = {"id": "ABC-111", "title": "Test"}

        # Mock call_agent_with_retry raising ValueError after retries exhausted
        mock_agent_retry.side_effect = ValueError("All 3 attempts failed. Last error: Could not extract valid JSON")

        result = execute_triage("ABC-111")

        assert result.success is False
        assert result.error is not None
        assert "Could not extract valid JSON" in result.error

    @patch("orchestrator.triage.fetch_issue")
    @patch("orchestrator.triage.update_issue")
    @patch("orchestrator.triage.call_agent_with_retry")
    def test_triage_duration_tracking(self, mock_agent_retry, mock_update, mock_fetch):
        """Test that triage tracks execution duration."""
        # Mock successful workflow
        mock_fetch.return_value = {"id": "ABC-222"}

        mock_agent_retry.side_effect = [
            ValidityAnalysis(
                is_valid=True,
                is_actionable=True,
                missing_context=[],
                reasoning="OK",
            ),
            SeverityAnalysis(
                severity="P2",
                complexity="medium",
                required_expertise=[],
                reasoning="OK",
            ),
        ]

        result = execute_triage("ABC-222")

        assert result.success is True
        assert result.duration > 0
        assert result.duration < 10  # Should be very fast with mocks

    @patch("orchestrator.triage.fetch_issue")
    @patch("orchestrator.triage.update_issue")
    @patch("orchestrator.triage.call_agent_with_retry")
    def test_triage_calls_correct_agents(self, mock_agent_retry, mock_update, mock_fetch):
        """Test that triage calls the correct agents in order."""
        # Mock successful workflow
        mock_fetch.return_value = {"id": "ABC-333"}

        mock_agent_retry.side_effect = [
            ValidityAnalysis(
                is_valid=True,
                is_actionable=True,
                missing_context=[],
                reasoning="OK",
            ),
            SeverityAnalysis(
                severity="P2",
                complexity="simple",
                required_expertise=[],
                reasoning="OK",
            ),
        ]

        execute_triage("ABC-333")

        # Verify agent calls
        assert mock_agent_retry.call_count == 2

        # First call should be analysis-expert
        first_call = mock_agent_retry.call_args_list[0]
        assert first_call.kwargs["agent_name"] == "analysis-expert"

        # Second call should be bug-hunter
        second_call = mock_agent_retry.call_args_list[1]
        assert second_call.kwargs["agent_name"] == "bug-hunter"


class TestFormatAiComment:
    """Test format_ai_comment() function."""

    def test_format_with_all_fields(self):
        """Test comment formatting with all fields populated."""
        validity = ValidityAnalysis(
            is_valid=True,
            is_actionable=True,
            missing_context=[],
            reasoning="Clear bug report with reproduction steps",
        )

        severity = SeverityAnalysis(
            severity="P1",
            complexity="medium",
            required_expertise=["Backend", "Database"],
            reasoning="Critical data loss issue",
        )

        comment = format_ai_comment(validity, severity)

        assert "## AI Triage Analysis" in comment
        assert "Valid" in comment
        assert "Actionable" in comment
        assert "P1" in comment
        assert "Medium" in comment
        assert "Backend, Database" in comment
        assert "Clear bug report" in comment
        assert "Critical data loss" in comment
        assert "*Generated by Orchestrator*" in comment

    def test_format_with_missing_context(self):
        """Test comment formatting with missing context."""
        validity = ValidityAnalysis(
            is_valid=True,
            is_actionable=False,
            missing_context=["Error logs", "Browser version"],
            reasoning="Need additional information",
        )

        severity = SeverityAnalysis(
            severity="P3",
            complexity="simple",
            required_expertise=[],
            reasoning="Low priority",
        )

        comment = format_ai_comment(validity, severity)

        assert "#### Missing Context" in comment
        assert "- Error logs" in comment
        assert "- Browser version" in comment

    def test_format_invalid_ticket(self):
        """Test comment formatting for invalid ticket."""
        validity = ValidityAnalysis(
            is_valid=False,
            is_actionable=False,
            missing_context=[],
            reasoning="Not a bug, user error",
        )

        severity = SeverityAnalysis(
            severity="P3",
            complexity="simple",
            required_expertise=[],
            reasoning="No action needed",
        )

        comment = format_ai_comment(validity, severity)

        assert "Invalid" in comment
        assert "Not Actionable" in comment
        assert "Not a bug" in comment

    def test_format_with_empty_expertise(self):
        """Test comment formatting with no required expertise."""
        validity = ValidityAnalysis(
            is_valid=True,
            is_actionable=True,
            missing_context=[],
            reasoning="Simple fix",
        )

        severity = SeverityAnalysis(
            severity="P2",
            complexity="simple",
            required_expertise=[],
            reasoning="Easy to resolve",
        )

        comment = format_ai_comment(validity, severity)

        assert "None" in comment  # Should show "None" for empty expertise


class TestSeverityToPriority:
    """Test severity_to_priority() function."""

    def test_p0_maps_to_urgent(self):
        """Test P0 severity maps to urgent priority."""
        assert severity_to_priority("P0") == 1

    def test_p1_maps_to_high(self):
        """Test P1 severity maps to high priority."""
        assert severity_to_priority("P1") == 2

    def test_p2_maps_to_medium(self):
        """Test P2 severity maps to medium priority."""
        assert severity_to_priority("P2") == 3

    def test_p3_maps_to_low(self):
        """Test P3 severity maps to low priority."""
        assert severity_to_priority("P3") == 4

    def test_unknown_severity_maps_to_none(self):
        """Test unknown severity maps to none priority."""
        assert severity_to_priority("UNKNOWN") == 0
        assert severity_to_priority("") == 0
