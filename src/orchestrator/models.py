"""Pydantic data models for orchestrator workflows."""

from datetime import datetime
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
    validity: ValidityAnalysis | None = Field(
        default=None, description="Validity analysis result (None if triage failed)"
    )
    severity: SeverityAnalysis | None = Field(
        default=None, description="Severity assessment result (None if triage failed)"
    )
    ai_comment: str = Field(..., description="Formatted AI analysis comment for Linear")
    success: bool = Field(..., description="Whether triage completed successfully")
    duration: float = Field(..., description="Total execution time in seconds")
    agents_used: list[str] = Field(default_factory=list, description="List of agents delegated to")
    error: str | None = None  # Error message if success=False


# Investigation Workflow Models


class Citation(BaseModel):
    """Single source citation for findings and recommendations."""

    source_type: Literal["linear_issue", "git_commit", "codebase", "logs", "pattern"] = Field(
        ..., description="Type of source being cited"
    )
    source_id: str = Field(..., min_length=1, description="Unique identifier for the source")
    source_url: str = Field(..., min_length=1, description="Direct URL to the source")
    excerpt: str = Field(..., min_length=1, description="Relevant excerpt from the source")
    retrieved_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(), description="Timestamp when citation was retrieved"
    )


class Finding(BaseModel):
    """Single finding from investigation with mandatory citations."""

    finding: str = Field(..., min_length=10, description="Description of the finding")
    confidence: Literal["low", "medium", "high"] = Field(..., description="Confidence level in this finding")
    citations: list[Citation] = Field(
        ...,
        min_length=1,
        description="Sources supporting this finding",  # MANDATORY: At least one citation required
    )


class Recommendation(BaseModel):
    """Actionable recommendation with mandatory citations."""

    recommendation: str = Field(..., min_length=10, description="The recommendation")
    reasoning: str = Field(..., min_length=10, description="Reasoning behind the recommendation")
    confidence: Literal["low", "medium", "high"] = Field(..., description="Confidence level")
    citations: list[Citation] = Field(
        ...,
        min_length=1,
        description="Evidence supporting this recommendation",  # MANDATORY: At least one citation required
    )


class PatternMatch(BaseModel):
    """Pattern from learning store matching current issue."""

    pattern_id: str = Field(..., description="Unique pattern identifier")
    description: str = Field(..., description="Pattern description")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Match confidence (0-1)")
    successful_resolutions: int = Field(..., ge=0, description="Number of times pattern led to resolution")
    citations: list[Citation] = Field(default_factory=list, description="Historical citations for pattern")


class InvestigationResult(BaseModel):
    """Complete result of investigation workflow execution."""

    issue_id: str = Field(..., description="Linear issue identifier")
    issue_url: str = Field(..., description="URL to Linear issue")
    findings: list[Finding] = Field(default_factory=list, description="Investigation findings")
    recommendations: list[Recommendation] = Field(default_factory=list, description="Actionable recommendations")
    pattern_matches: list[PatternMatch] = Field(
        default_factory=list, description="Matching patterns from learning store"
    )
    success: bool = Field(..., description="Whether investigation completed successfully")
    duration: float = Field(..., description="Total execution time in seconds")
    agents_used: list[str] = Field(default_factory=list, description="List of agents delegated to")
    similar_issues_count: int = Field(default=0, description="Number of similar issues found")
    citations_count: int = Field(default=0, description="Total citations across all findings/recommendations")
    error: str | None = None  # Error message if success=False
