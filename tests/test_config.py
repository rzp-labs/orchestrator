"""Tests for configuration module."""

import os

from orchestrator.config import get_linear_writes_enabled
from orchestrator.config import get_write_mode_display


class TestLinearWritesConfig:
    """Test LINEAR_ENABLE_WRITES configuration."""

    def test_writes_disabled_by_default(self) -> None:
        """Writes should be disabled when env var not set."""
        if "LINEAR_ENABLE_WRITES" in os.environ:
            del os.environ["LINEAR_ENABLE_WRITES"]
        assert get_linear_writes_enabled() is False
        assert get_write_mode_display() == "READ-ONLY"

    def test_writes_enabled_with_true(self) -> None:
        """Writes enabled when LINEAR_ENABLE_WRITES=true."""
        os.environ["LINEAR_ENABLE_WRITES"] = "true"
        assert get_linear_writes_enabled() is True
        assert get_write_mode_display() == "WRITE"

    def test_writes_enabled_with_1(self) -> None:
        """Writes enabled when LINEAR_ENABLE_WRITES=1."""
        os.environ["LINEAR_ENABLE_WRITES"] = "1"
        assert get_linear_writes_enabled() is True

    def test_writes_enabled_with_yes(self) -> None:
        """Writes enabled when LINEAR_ENABLE_WRITES=yes."""
        os.environ["LINEAR_ENABLE_WRITES"] = "yes"
        assert get_linear_writes_enabled() is True

    def test_writes_disabled_with_false(self) -> None:
        """Writes disabled when LINEAR_ENABLE_WRITES=false."""
        os.environ["LINEAR_ENABLE_WRITES"] = "false"
        assert get_linear_writes_enabled() is False

    def test_writes_disabled_with_invalid_value(self) -> None:
        """Writes disabled with invalid env var value."""
        os.environ["LINEAR_ENABLE_WRITES"] = "maybe"
        assert get_linear_writes_enabled() is False

    def test_case_insensitive(self) -> None:
        """Env var check is case-insensitive."""
        os.environ["LINEAR_ENABLE_WRITES"] = "TRUE"
        assert get_linear_writes_enabled() is True
