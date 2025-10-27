"""Tests for Claude Code hooks."""

import json
import subprocess
import sys
from pathlib import Path


class TestHookLogger:
    """Test HookLogger class."""

    def test_logger_creates_log_directory(self, tmp_path, monkeypatch):
        """Test that logger creates logs directory."""
        monkeypatch.chdir(tmp_path)

        # Import after changing directory
        sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "tools"))
        from hook_logger import HookLogger  # type: ignore[import-not-found]

        HookLogger("test_hook")  # Creates logger and log directory

        assert (tmp_path / "logs").exists()
        assert (tmp_path / "logs").is_dir()

    def test_logger_creates_dated_log_file(self, tmp_path, monkeypatch):
        """Test that logger creates dated log file with correct naming."""
        monkeypatch.chdir(tmp_path)

        sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "tools"))
        from hook_logger import HookLogger  # type: ignore[import-not-found]

        logger = HookLogger("test_hook")
        logger.info("Test")  # Write to create file

        # Check log file exists with date format
        assert logger.log_file.exists()
        assert "test_hook_" in logger.log_file.name
        assert logger.log_file.name.endswith(".log")

    def test_info_writes_to_log(self, tmp_path, monkeypatch):
        """Test that info() writes INFO messages to log."""
        monkeypatch.chdir(tmp_path)

        sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "tools"))
        from hook_logger import HookLogger  # type: ignore[import-not-found]

        logger = HookLogger("test_hook")
        logger.info("Test message")

        log_content = logger.log_file.read_text()
        assert "[INFO] Test message" in log_content
        assert "] [INFO]" in log_content  # Timestamp present

    def test_error_writes_to_log(self, tmp_path, monkeypatch):
        """Test that error() writes ERROR messages to log."""
        monkeypatch.chdir(tmp_path)

        sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "tools"))
        from hook_logger import HookLogger  # type: ignore[import-not-found]

        logger = HookLogger("test_hook")
        logger.error("Error message")

        log_content = logger.log_file.read_text()
        assert "[ERROR] Error message" in log_content

    def test_debug_writes_to_log(self, tmp_path, monkeypatch):
        """Test that debug() writes DEBUG messages to log."""
        monkeypatch.chdir(tmp_path)

        sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "tools"))
        from hook_logger import HookLogger  # type: ignore[import-not-found]

        logger = HookLogger("test_hook")
        logger.debug("Debug message")

        log_content = logger.log_file.read_text()
        assert "[DEBUG] Debug message" in log_content

    def test_multiple_log_entries(self, tmp_path, monkeypatch):
        """Test writing multiple log entries."""
        monkeypatch.chdir(tmp_path)

        sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "tools"))
        from hook_logger import HookLogger  # type: ignore[import-not-found]

        logger = HookLogger("test_hook")
        logger.info("First message")
        logger.error("Second message")
        logger.debug("Third message")

        log_content = logger.log_file.read_text()
        lines = log_content.strip().split("\n")
        assert len(lines) == 3
        assert "[INFO] First message" in lines[0]
        assert "[ERROR] Second message" in lines[1]
        assert "[DEBUG] Third message" in lines[2]


class TestPostTriageHook:
    """Test post-triage hook."""

    def test_hook_success_execution(self, tmp_path):
        """Test successful hook execution."""
        input_data = {
            "ticket_id": "ABC-123",
            "duration": 5.2,
            "success": True,
            "agents_used": ["analysis-expert", "bug-hunter"],
        }

        # Run hook as subprocess
        hook_path = Path(__file__).parent.parent / ".claude" / "tools" / "hook_post_triage.py"
        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["metadata"]["logged"] is True

    def test_hook_creates_metrics_file(self, tmp_path):
        """Test that hook creates metrics JSONL file."""
        input_data = {
            "ticket_id": "ABC-456",
            "duration": 3.1,
            "success": True,
            "agents_used": ["analysis-expert"],
        }

        hook_path = Path(__file__).parent.parent / ".claude" / "tools" / "hook_post_triage.py"
        subprocess.run(
            [sys.executable, str(hook_path)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )

        # Check metrics file was created
        metrics_file = tmp_path / "logs" / "triage_metrics.jsonl"
        assert metrics_file.exists()

        # Verify content
        content = metrics_file.read_text()
        metrics = json.loads(content.strip())
        assert metrics["ticket_id"] == "ABC-456"
        assert metrics["duration"] == 3.1
        assert metrics["success"] is True

    def test_hook_failure_execution(self, tmp_path):
        """Test hook execution with failure result."""
        input_data = {
            "ticket_id": "ABC-789",
            "duration": 1.5,
            "success": False,
            "agents_used": [],
        }

        hook_path = Path(__file__).parent.parent / ".claude" / "tools" / "hook_post_triage.py"
        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )

        # Hook should still succeed even if triage failed
        assert result.returncode == 0

        # Check metrics logged with success=False
        metrics_file = tmp_path / "logs" / "triage_metrics.jsonl"
        content = metrics_file.read_text()
        metrics = json.loads(content.strip())
        assert metrics["success"] is False

    def test_hook_appends_to_metrics(self, tmp_path):
        """Test that hook appends to existing metrics file."""
        input_data_1 = {"ticket_id": "ABC-111", "duration": 2.0, "success": True, "agents_used": []}
        input_data_2 = {"ticket_id": "ABC-222", "duration": 3.0, "success": True, "agents_used": []}

        hook_path = Path(__file__).parent.parent / ".claude" / "tools" / "hook_post_triage.py"

        # Run hook twice
        subprocess.run(
            [sys.executable, str(hook_path)],
            input=json.dumps(input_data_1),
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )
        subprocess.run(
            [sys.executable, str(hook_path)],
            input=json.dumps(input_data_2),
            capture_output=True,
            text=True,
            cwd=tmp_path,
        )

        # Check both entries are in file
        metrics_file = tmp_path / "logs" / "triage_metrics.jsonl"
        lines = metrics_file.read_text().strip().split("\n")
        assert len(lines) == 2

        metrics_1 = json.loads(lines[0])
        metrics_2 = json.loads(lines[1])
        assert metrics_1["ticket_id"] == "ABC-111"
        assert metrics_2["ticket_id"] == "ABC-222"
