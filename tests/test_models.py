"""Tests for Pydantic data models."""

import pytest

from orchestrator.models import SeverityAnalysis, TriageResult, ValidityAnalysis


def test_validity_analysis_valid(validity_analysis):
    """Test ValidityAnalysis with valid data."""
    analysis = ValidityAnalysis(**validity_analysis)
    assert analysis.is_valid is True
    assert analysis.is_actionable is True
    assert analysis.missing_context == []
    assert len(analysis.reasoning) > 0


def test_validity_analysis_with_missing_context():
    """Test ValidityAnalysis with missing context."""
    data = {
        "is_valid": True,
        "is_actionable": False,
        "missing_context": ["Reproduction steps", "Error logs"],
        "reasoning": "Valid issue but needs more information",
    }
    analysis = ValidityAnalysis(**data)
    assert analysis.is_actionable is False
    assert len(analysis.missing_context) == 2


def test_severity_analysis_valid(severity_analysis):
    """Test SeverityAnalysis with valid data."""
    analysis = SeverityAnalysis(**severity_analysis)
    assert analysis.severity == "P1"
    assert analysis.complexity == "medium"
    assert "Backend" in analysis.required_expertise


def test_severity_analysis_all_priorities():
    """Test SeverityAnalysis accepts all valid priority levels."""
    for priority in ["P0", "P1", "P2", "P3"]:
        data = {
            "severity": priority,
            "complexity": "simple",
            "required_expertise": [],
            "reasoning": "Test",
        }
        analysis = SeverityAnalysis(**data)
        assert analysis.severity == priority


def test_severity_analysis_invalid_severity():
    """Test SeverityAnalysis rejects invalid severity."""
    data = {
        "severity": "P5",
        "complexity": "medium",
        "required_expertise": [],
        "reasoning": "Test",
    }
    with pytest.raises(ValueError):
        SeverityAnalysis(**data)


def test_severity_analysis_invalid_complexity():
    """Test SeverityAnalysis rejects invalid complexity."""
    data = {
        "severity": "P1",
        "complexity": "very_hard",
        "required_expertise": [],
        "reasoning": "Test",
    }
    with pytest.raises(ValueError):
        SeverityAnalysis(**data)


def test_triage_result_success(validity_analysis, severity_analysis):
    """Test TriageResult with successful triage."""
    result = TriageResult(
        ticket_id="ABC-123",
        ticket_url="https://linear.app/issue/ABC-123",
        validity=ValidityAnalysis(**validity_analysis),
        severity=SeverityAnalysis(**severity_analysis),
        ai_comment="Test comment",
        success=True,
        duration=23.5,
        agents_used=["analysis-expert", "bug-hunter"],
    )
    assert result.success is True
    assert result.validity is not None
    assert result.severity is not None
    assert result.error is None


def test_triage_result_failure():
    """Test TriageResult with failed triage."""
    result = TriageResult(
        ticket_id="ABC-123",
        ticket_url="https://linear.app/issue/ABC-123",
        validity=None,
        severity=None,
        ai_comment="",
        success=False,
        duration=5.2,
        agents_used=[],
        error="Ticket not found",
    )
    assert result.success is False
    assert result.validity is None
    assert result.severity is None
    assert result.error == "Ticket not found"
