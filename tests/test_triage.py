"""Tests for triage workflow orchestration."""

import subprocess
from unittest.mock import MagicMock, patch

from orchestrator.models import SeverityAnalysis, ValidityAnalysis
from orchestrator.triage import execute_triage, format_ai_comment


class TestExecuteTriage:
    """Test execute_triage() function."""

    @patch("orchestrator.triage.run_cli_command")
    @patch("orchestrator.triage.run_agent")
    @patch("orchestrator.triage.parse_llm_json")
    def test_successful_triage(self, mock_parse, mock_agent, mock_cli):
        """Test complete successful triage workflow."""
        # Mock Linear ticket fetch
        mock_ticket_result = MagicMock()
        mock_ticket_result.stdout = '{"id": "ABC-123", "title": "Test bug"}'

        # Mock Linear update (second call to run_cli_command)
        mock_update_result = MagicMock()
        mock_update_result.stdout = "Updated"

        mock_cli.side_effect = [mock_ticket_result, mock_update_result]

        # Mock agent responses
        mock_agent.side_effect = [
            '{"is_valid": true, "is_actionable": true, "missing_context": [], "reasoning": "Valid"}',
            '{"severity": "P1", "complexity": "medium", "required_expertise": ["Backend"], "reasoning": "Critical"}',
        ]

        # Mock JSON parsing
        mock_parse.side_effect = [
            {
                "is_valid": True,
                "is_actionable": True,
                "missing_context": [],
                "reasoning": "Valid bug report",
            },
            {
                "severity": "P1",
                "complexity": "medium",
                "required_expertise": ["Backend"],
                "reasoning": "Critical issue",
            },
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

    @patch("orchestrator.triage.run_cli_command")
    @patch("orchestrator.triage.run_agent")
    @patch("orchestrator.triage.parse_llm_json")
    def test_triage_with_missing_context(self, mock_parse, mock_agent, mock_cli):
        """Test triage with validity requiring missing context."""
        # Mock Linear operations
        mock_ticket_result = MagicMock()
        mock_ticket_result.stdout = '{"id": "ABC-456", "title": "Incomplete report"}'
        mock_update_result = MagicMock()
        mock_update_result.stdout = "Updated"
        mock_cli.side_effect = [mock_ticket_result, mock_update_result]

        # Mock agent responses
        mock_agent.side_effect = [
            '{"is_valid": true, "is_actionable": false}',
            '{"severity": "P3", "complexity": "simple"}',
        ]

        # Mock JSON parsing with missing context
        mock_parse.side_effect = [
            {
                "is_valid": True,
                "is_actionable": False,
                "missing_context": ["Reproduction steps", "Error logs"],
                "reasoning": "Need more information",
            },
            {
                "severity": "P3",
                "complexity": "simple",
                "required_expertise": [],
                "reasoning": "Low priority",
            },
        ]

        result = execute_triage("ABC-456")

        assert result.success is True
        assert result.validity is not None
        assert result.validity.is_actionable is False
        assert len(result.validity.missing_context) == 2
        assert "Reproduction steps" in result.validity.missing_context

    @patch("orchestrator.triage.run_cli_command")
    def test_triage_fails_on_ticket_fetch_error(self, mock_cli):
        """Test that triage handles Linear fetch errors gracefully."""
        mock_cli.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["linear-cli"], stderr="Ticket not found"
        )

        result = execute_triage("INVALID-999")

        assert result.success is False
        assert result.error is not None
        assert "returned non-zero exit status" in result.error
        assert result.validity is None
        assert result.severity is None

    @patch("orchestrator.triage.run_cli_command")
    @patch("orchestrator.triage.run_agent")
    def test_triage_fails_on_agent_error(self, mock_agent, mock_cli):
        """Test that triage handles agent execution errors gracefully."""
        # Mock successful ticket fetch
        mock_ticket_result = MagicMock()
        mock_ticket_result.stdout = '{"id": "ABC-789", "title": "Test"}'
        mock_cli.return_value = mock_ticket_result

        # Mock agent failure
        mock_agent.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["claude"], stderr="Agent failed"
        )

        result = execute_triage("ABC-789")

        assert result.success is False
        assert result.error is not None
        assert result.validity is None
        assert result.severity is None

    @patch("orchestrator.triage.run_cli_command")
    @patch("orchestrator.triage.run_agent")
    @patch("orchestrator.triage.parse_llm_json")
    def test_triage_fails_on_invalid_json(self, mock_parse, mock_agent, mock_cli):
        """Test that triage handles invalid LLM JSON gracefully."""
        # Mock successful ticket fetch
        mock_ticket_result = MagicMock()
        mock_ticket_result.stdout = '{"id": "ABC-111", "title": "Test"}'
        mock_cli.return_value = mock_ticket_result

        # Mock agent response
        mock_agent.return_value = "Not valid JSON"

        # Mock parse_llm_json raising ValueError
        mock_parse.side_effect = ValueError("Could not extract valid JSON")

        result = execute_triage("ABC-111")

        assert result.success is False
        assert result.error is not None
        assert "Could not extract valid JSON" in result.error

    @patch("orchestrator.triage.run_cli_command")
    @patch("orchestrator.triage.run_agent")
    @patch("orchestrator.triage.parse_llm_json")
    def test_triage_duration_tracking(self, mock_parse, mock_agent, mock_cli):
        """Test that triage tracks execution duration."""
        # Mock successful workflow
        mock_ticket_result = MagicMock()
        mock_ticket_result.stdout = '{"id": "ABC-222"}'
        mock_update_result = MagicMock()
        mock_update_result.stdout = "Updated"
        mock_cli.side_effect = [mock_ticket_result, mock_update_result]

        mock_agent.side_effect = ["validity json", "severity json"]
        mock_parse.side_effect = [
            {
                "is_valid": True,
                "is_actionable": True,
                "missing_context": [],
                "reasoning": "OK",
            },
            {
                "severity": "P2",
                "complexity": "medium",
                "required_expertise": [],
                "reasoning": "OK",
            },
        ]

        result = execute_triage("ABC-222")

        assert result.success is True
        assert result.duration > 0
        assert result.duration < 10  # Should be very fast with mocks

    @patch("orchestrator.triage.run_cli_command")
    @patch("orchestrator.triage.run_agent")
    @patch("orchestrator.triage.parse_llm_json")
    def test_triage_calls_correct_agents(self, mock_parse, mock_agent, mock_cli):
        """Test that triage calls the correct agents in order."""
        # Mock successful workflow
        mock_ticket_result = MagicMock()
        mock_ticket_result.stdout = '{"id": "ABC-333"}'
        mock_update_result = MagicMock()
        mock_update_result.stdout = "Updated"
        mock_cli.side_effect = [mock_ticket_result, mock_update_result]

        mock_agent.side_effect = ["validity", "severity"]
        mock_parse.side_effect = [
            {
                "is_valid": True,
                "is_actionable": True,
                "missing_context": [],
                "reasoning": "OK",
            },
            {
                "severity": "P2",
                "complexity": "simple",
                "required_expertise": [],
                "reasoning": "OK",
            },
        ]

        execute_triage("ABC-333")

        # Verify agent calls
        assert mock_agent.call_count == 2

        # First call should be analysis-expert
        first_call = mock_agent.call_args_list[0]
        assert first_call.kwargs["agent_name"] == "analysis-expert"

        # Second call should be bug-hunter
        second_call = mock_agent.call_args_list[1]
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
