"""Pytest fixtures for orchestrator tests."""

import pytest


@pytest.fixture
def ticket_json() -> dict:
    """Sample Linear ticket JSON for testing."""
    return {
        "id": "ABC-123",
        "title": "User login fails with 500 error",
        "description": "When users try to login with valid credentials, they receive a 500 internal server error.",
        "priority": "P2",
        "status": "Todo",
        "labels": ["bug", "backend"],
    }


@pytest.fixture
def validity_analysis() -> dict:
    """Sample validity analysis for testing."""
    return {
        "is_valid": True,
        "is_actionable": True,
        "missing_context": [],
        "reasoning": "Valid issue with sufficient detail for investigation. Clear reproduction steps provided.",
    }


@pytest.fixture
def severity_analysis() -> dict:
    """Sample severity assessment for testing."""
    return {
        "severity": "P1",
        "complexity": "medium",
        "required_expertise": ["Backend", "Database"],
        "reasoning": "High priority authentication issue affecting all users. Moderate complexity requiring backend investigation.",
    }
