"""Pydantic data models for orchestrator workflows."""

from typing import Literal

from pydantic import BaseModel, Field


class TriageInput(BaseModel):
    """Input for support triage workflow."""

    ticket_id: str = Field(..., description="Linear ticket identifier (e.g., ABC-123)")


class ValidityAnalysis(BaseModel):
    """Result of ticket validity analysis."""

    is_valid: bool = Field(..., description="Whether this is a valid bug/issue")
    is_actionable: bool = Field(..., description="Whether there is sufficient information to act")
    missing_context: list[str] = Field(default_factory=list, description="Additional context needed")
    reasoning: str = Field(..., description="Explanation of validity determination")


class SeverityAnalysis(BaseModel):
    """Result of ticket severity assessment."""

    severity: Literal["P0", "P1", "P2", "P3"] = Field(..., description="Priority level (P0=critical, P3=low)")
    complexity: Literal["simple", "medium", "complex"] = Field(..., description="Estimated complexity")
    required_expertise: list[str] = Field(default_factory=list, description="Required skills/expertise areas")
    reasoning: str = Field(..., description="Explanation of severity assessment")


class TriageResult(BaseModel):
    """Complete result of triage workflow execution."""

    ticket_id: str = Field(..., description="Linear ticket identifier")
    ticket_url: str = Field(..., description="URL to Linear ticket")
    validity: ValidityAnalysis | None = Field(default=None, description="Validity analysis result (None if triage failed)")
    severity: SeverityAnalysis | None = Field(default=None, description="Severity assessment result (None if triage failed)")
    ai_comment: str = Field(..., description="Formatted AI analysis comment for Linear")
    success: bool = Field(..., description="Whether triage completed successfully")
    duration: float = Field(..., description="Total execution time in seconds")
    agents_used: list[str] = Field(default_factory=list, description="List of agents delegated to")
    error: str | None = None  # Error message if success=False
