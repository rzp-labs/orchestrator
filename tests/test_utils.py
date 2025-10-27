"""Tests for defensive utilities module."""

import subprocess
from unittest.mock import patch

import pytest

from orchestrator.utils import parse_llm_json, run_agent, run_cli_command


class TestParseLlmJson:
    """Test parse_llm_json() function."""

    def test_parse_direct_json(self):
        """Test parsing direct JSON response."""
        response = '{"key": "value", "number": 42}'
        result = parse_llm_json(response)
        assert result == {"key": "value", "number": 42}

    def test_parse_markdown_json_block(self):
        """Test parsing JSON wrapped in markdown code block."""
        response = """
Here is the analysis:

```json
{
    "is_valid": true,
    "reasoning": "Clear bug report"
}
```

Let me know if you need more details.
"""
        result = parse_llm_json(response)
        assert result == {"is_valid": True, "reasoning": "Clear bug report"}

    def test_parse_markdown_without_language(self):
        """Test parsing JSON in markdown block without language tag."""
        response = """
```
{"severity": "P1", "complexity": "medium"}
```
"""
        result = parse_llm_json(response)
        assert result == {"severity": "P1", "complexity": "medium"}

    def test_parse_json_with_text_before_and_after(self):
        """Test extracting JSON from response with explanatory text."""
        response = """
Based on my analysis, here is the result:

{"is_actionable": false, "missing_context": ["logs", "steps"]}

This indicates we need more information.
"""
        result = parse_llm_json(response)
        assert result == {"is_actionable": False, "missing_context": ["logs", "steps"]}

    def test_parse_nested_json(self):
        """Test parsing nested JSON structures."""
        response = """
```json
{
    "ticket_id": "ABC-123",
    "validity": {
        "is_valid": true,
        "reasoning": "Good"
    },
    "severity": {
        "level": "P2"
    }
}
```
"""
        result = parse_llm_json(response)
        assert result["ticket_id"] == "ABC-123"
        assert result["validity"]["is_valid"] is True
        assert result["severity"]["level"] == "P2"

    def test_parse_json_array(self):
        """Test parsing JSON array."""
        response = '["item1", "item2", "item3"]'
        result = parse_llm_json(response)
        assert result == ["item1", "item2", "item3"]

    def test_parse_json_with_multiline_strings(self):
        """Test parsing JSON with multiline string values."""
        response = """
```json
{
    "reasoning": "This is a multi-line\\nexplanation that\\nspans several lines",
    "valid": true
}
```
"""
        result = parse_llm_json(response)
        assert "multi-line" in result["reasoning"]
        assert result["valid"] is True

    def test_empty_response_raises_error(self):
        """Test that empty response raises ValueError."""
        with pytest.raises(ValueError, match="Empty response"):
            parse_llm_json("")

    def test_whitespace_only_raises_error(self):
        """Test that whitespace-only response raises ValueError."""
        with pytest.raises(ValueError, match="Empty response"):
            parse_llm_json("   \n\t  ")

    def test_no_json_raises_error(self):
        """Test that response without JSON raises ValueError."""
        response = "This is just plain text with no JSON at all."
        with pytest.raises(ValueError, match="Could not extract valid JSON"):
            parse_llm_json(response)

    def test_malformed_json_raises_error(self):
        """Test that malformed JSON raises ValueError."""
        response = '{"key": "value", "missing_close"'
        with pytest.raises(ValueError, match="Could not extract valid JSON"):
            parse_llm_json(response)

    def test_multiple_json_objects_returns_first_valid(self):
        """Test that multiple JSON objects returns the longest valid one."""
        response = """
Small: {"a": 1}

Larger and complete:
```json
{
    "is_valid": true,
    "is_actionable": true,
    "reasoning": "Complete analysis"
}
```
"""
        result = parse_llm_json(response)
        # Should return the larger, more complete JSON
        assert "reasoning" in result
        assert result["is_valid"] is True

    def test_pathological_multi_json_with_text_between(self):
        """Test pathological case: multiple JSON objects with invalid text between them.

        This tests the edge case identified by zen-architect where greedy regex
        patterns might match across multiple JSON objects incorrectly.
        """
        response = 'First: {"a": 1} and some invalid text second: {"b": {"c": 2}}'

        result = parse_llm_json(response)

        # Should extract one of the valid JSON objects, not invalid combination
        # Either {"a": 1} or {"b": {"c": 2}} is acceptable
        assert isinstance(result, dict)
        assert ("a" in result and result["a"] == 1) or ("b" in result and result["b"]["c"] == 2)


class TestRunCliCommand:
    """Test run_cli_command() function."""

    @patch("orchestrator.utils.subprocess.run")
    def test_successful_command(self, mock_run):
        """Test running a successful command."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["echo", "hello"],
            returncode=0,
            stdout="hello\n",
            stderr="",
        )

        result = run_cli_command(["echo", "hello"])

        assert result.returncode == 0
        assert result.stdout == "hello\n"
        mock_run.assert_called_once()

    @patch("orchestrator.utils.subprocess.run")
    def test_command_with_custom_timeout(self, mock_run):
        """Test command with custom timeout."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["sleep", "1"],
            returncode=0,
            stdout="",
            stderr="",
        )

        run_cli_command(["sleep", "1"], timeout=60)

        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["timeout"] == 60

    @patch("orchestrator.utils.subprocess.run")
    def test_command_failure_with_check_true(self, mock_run):
        """Test that failed command raises CalledProcessError when check=True."""
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["false"],
            stderr="command failed",
        )

        with pytest.raises(subprocess.CalledProcessError):
            run_cli_command(["false"], check=True)

    @patch("orchestrator.utils.subprocess.run")
    def test_command_failure_with_check_false(self, mock_run):
        """Test that failed command returns result when check=False."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["false"],
            returncode=1,
            stdout="",
            stderr="error",
        )

        result = run_cli_command(["false"], check=False)

        assert result.returncode == 1
        assert result.stderr == "error"

    @patch("orchestrator.utils.subprocess.run")
    def test_command_timeout(self, mock_run):
        """Test that timeout is raised when command exceeds timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["sleep", "1000"],
            timeout=1,
        )

        with pytest.raises(subprocess.TimeoutExpired):
            run_cli_command(["sleep", "1000"], timeout=1)

    @patch("orchestrator.utils.subprocess.run")
    def test_command_not_found(self, mock_run):
        """Test that FileNotFoundError is raised for missing executable."""
        mock_run.side_effect = FileNotFoundError("command not found")

        with pytest.raises(FileNotFoundError):
            run_cli_command(["nonexistent-command"])

    @patch("orchestrator.utils.subprocess.run")
    def test_command_captures_output(self, mock_run):
        """Test that command output is captured."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["gh", "issue", "view", "123"],
            returncode=0,
            stdout="Issue #123: Test issue\n",
            stderr="",
        )

        result = run_cli_command(["gh", "issue", "view", "123"])

        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["capture_output"] is True
        assert call_kwargs["text"] is True
        assert result.stdout == "Issue #123: Test issue\n"


class TestRunAgent:
    """Test run_agent() function."""

    @patch("orchestrator.utils.run_cli_command")
    def test_run_agent_success(self, mock_run_cli):
        """Test successful agent execution."""
        mock_result = subprocess.CompletedProcess(
            args=["claude", "--print", "--agents", "...", "task"],
            returncode=0,
            stdout="Agent analysis result\n",
            stderr="",
        )
        mock_run_cli.return_value = mock_result

        result = run_agent("analysis-expert", "Analyze this ticket")

        assert result == "Agent analysis result\n"
        # Verify run_cli_command was called with correct structure
        call_args = mock_run_cli.call_args
        assert call_args[0][0][0] == "claude"
        assert call_args[0][0][1] == "--print"
        assert call_args[0][0][2] == "--agents"

    @patch("orchestrator.utils.run_cli_command")
    def test_run_agent_with_custom_timeout(self, mock_run_cli):
        """Test agent execution with custom timeout."""
        mock_result = subprocess.CompletedProcess(
            args=["claude"],
            returncode=0,
            stdout="result",
            stderr="",
        )
        mock_run_cli.return_value = mock_result

        run_agent("bug-hunter", "Find bugs", timeout=120)

        # Verify timeout was passed
        call_kwargs = mock_run_cli.call_args.kwargs
        assert call_kwargs["timeout"] == 120

    @patch("orchestrator.utils.run_cli_command")
    def test_run_agent_logs_delegation(self, mock_run_cli, caplog):
        """Test that run_agent logs the delegation."""
        import logging

        caplog.set_level(logging.INFO)

        mock_result = subprocess.CompletedProcess(
            args=["claude"],
            returncode=0,
            stdout="result",
            stderr="",
        )
        mock_run_cli.return_value = mock_result

        run_agent("synthesis-master", "Synthesize insights")

        # Check that logging occurred
        assert "Delegating to synthesis-master" in caplog.text

    @patch("orchestrator.utils.run_cli_command")
    def test_run_agent_failure(self, mock_run_cli):
        """Test that run_agent propagates CLI command failures."""
        mock_run_cli.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["claude"],
            stderr="Agent execution failed",
        )

        with pytest.raises(subprocess.CalledProcessError):
            run_agent("analysis-expert", "Task")
