"""Configuration management for orchestrator.

This module provides centralized configuration for the orchestrator,
including control over Linear write operations via environment variables.
"""

import os


def get_linear_writes_enabled() -> bool:
    """Check if Linear write operations are enabled.

    Reads LINEAR_ENABLE_WRITES environment variable.
    Values 'true', '1', 'yes' (case-insensitive) enable writes.
    All other values (including unset) disable writes.

    Returns:
        bool: True if writes enabled, False otherwise (default)
    """
    value = os.getenv("LINEAR_ENABLE_WRITES", "false").lower()
    return value in ("true", "1", "yes")


def get_write_mode_display() -> str:
    """Get human-readable write mode for display.

    Returns:
        str: "READ-ONLY" or "WRITE"
    """
    return "WRITE" if get_linear_writes_enabled() else "READ-ONLY"
