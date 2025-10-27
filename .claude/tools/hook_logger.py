"""Shared logging utility for Claude Code hooks.

Provides simple file-based logging for hooks with automatic
log file management and timestamping.
"""

from datetime import datetime
from pathlib import Path


class HookLogger:
    """File-based logging for hooks.

    Creates daily log files in logs/ directory with format:
    logs/{hook_name}_{YYYYMMDD}.log

    Each log entry is timestamped with ISO format.
    """

    def __init__(self, hook_name: str):
        """Initialize logger for specific hook.

        Args:
            hook_name: Name of the hook (used in log filename)
        """
        self.hook_name = hook_name
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)

        date_str = datetime.now().strftime("%Y%m%d")
        self.log_file = self.log_dir / f"{hook_name}_{date_str}.log"

    def info(self, message: str) -> None:
        """Log info level message.

        Args:
            message: Message to log
        """
        self._write(f"[INFO] {message}")

    def error(self, message: str) -> None:
        """Log error level message.

        Args:
            message: Error message to log
        """
        self._write(f"[ERROR] {message}")

    def debug(self, message: str) -> None:
        """Log debug level message.

        Args:
            message: Debug message to log
        """
        self._write(f"[DEBUG] {message}")

    def _write(self, message: str) -> None:
        """Write to log file with timestamp.

        Args:
            message: Formatted message to write
        """
        timestamp = datetime.now().isoformat()
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
