"""Investigation orchestration module.

Orchestrates the complete investigation workflow:
1. Fetch issue from Linear
2. Research Linear history for similar issues
3. Check learning store for matching patterns
4. Synthesize findings via AI agent (STUBBED)
5. Generate recommendations via AI agent (STUBBED)
6. Record new patterns to learning store
7. Save investigation results to markdown file
"""

import logging
import time
from pathlib import Path
from typing import Any

from orchestrator.citation_tracker import CitationTracker
from orchestrator.learning_store import LearningStore
from orchestrator.linear_client import fetch_issue
from orchestrator.linear_history import LinearHistoryResearcher
from orchestrator.models import Finding, InvestigationResult, PatternMatch, Recommendation

logger = logging.getLogger(__name__)


def execute_investigation(issue_id: str) -> InvestigationResult:
    """Execute complete investigation workflow.

    Workflow Steps:
    1. Fetch issue from Linear
    2. Research Linear history for similar issues
    3. Check learning store for matching patterns
    4. Synthesize findings via AI agent (with mandatory citations)
    5. Generate recommendations via AI agent (with mandatory citations)
    6. Record new patterns to learning store
    7. Save investigation results to markdown file

    Args:
        issue_id: Linear issue ID (e.g., "ABC-123")

    Returns:
        InvestigationResult with all findings, recommendations, and citations

    Error Handling:
        - If any step fails, record error and return partial results
        - success=False indicates failure
        - error field contains error message
        - Partial data (findings, recommendations) preserved when possible
    """
    start_time = time.time()
    investigation_logger = logging.getLogger(f"investigation.{issue_id}")

    try:
        # Step 1: Fetch issue from Linear
        investigation_logger.info(f"Fetching issue {issue_id} from Linear")
        issue_data = fetch_issue(issue_id)

        # Step 2: Research Linear history for similar issues
        investigation_logger.info("Researching Linear history for similar issues")
        history_researcher = LinearHistoryResearcher()
        similar_issues = history_researcher.find_similar_issues(issue_id, max_results=50)

        # Step 3: Check learning store for matching patterns
        investigation_logger.info("Checking learning store for matching patterns")
        pattern_store = LearningStore()
        issue_description = issue_data.get("description", "")
        pattern_matches = pattern_store.find_matching_patterns(issue_description, min_confidence=0.7)

        # Step 4: Synthesize findings via AI agent
        investigation_logger.info("Synthesizing findings")
        findings = _synthesize_findings(issue_data, similar_issues, pattern_matches, investigation_logger)

        # Step 5: Generate recommendations via AI agent
        investigation_logger.info("Generating recommendations")
        recommendations = _generate_recommendations(issue_data, findings, pattern_matches, investigation_logger)

        # Step 6: Record new patterns to learning store
        investigation_logger.info("Recording patterns to learning store")
        confidence_map = {"low": 0.3, "medium": 0.6, "high": 0.9}
        for recommendation in recommendations:
            if confidence_map[recommendation.confidence] >= 0.7:  # Only record high-confidence patterns
                pattern_store.record_pattern(
                    issue_pattern=recommendation.recommendation,
                    recommendation=recommendation.reasoning,
                    citations=recommendation.citations,
                    outcome=None,  # Will be updated when issue closes
                )

        # Step 7: Build InvestigationResult
        duration = time.time() - start_time
        citations_count = sum(len(f.citations) for f in findings) + sum(len(r.citations) for r in recommendations)

        result = InvestigationResult(
            issue_id=issue_id,
            issue_url=f"https://linear.app/issue/{issue_id}",  # Construct URL
            findings=findings,
            recommendations=recommendations,
            pattern_matches=pattern_matches,  # Keep as list[PatternMatch]
            agents_used=["synthesis-master"],  # STUBBED - will be actual agents later
            similar_issues_count=len(similar_issues),
            citations_count=citations_count,
            success=True,
            duration=duration,
        )

        # Step 8: Save investigation results
        investigation_logger.info("Saving investigation results")
        _save_investigation(result, investigation_logger)

        investigation_logger.info(f"Investigation complete in {duration:.2f}s")
        return result

    except Exception as e:
        duration = time.time() - start_time
        investigation_logger.error(f"Investigation failed: {e}", exc_info=True)

        # Return partial results with error
        return InvestigationResult(
            issue_id=issue_id,
            issue_url=f"https://linear.app/issue/{issue_id}",
            findings=[],
            recommendations=[],
            pattern_matches=[],
            agents_used=[],
            similar_issues_count=0,
            citations_count=0,
            success=False,
            error=str(e),
            duration=duration,
        )


def _synthesize_findings(
    issue_data: dict[str, Any],
    similar_issues: list[dict[str, str]],
    pattern_matches: list[PatternMatch],
    logger: logging.Logger,
) -> list[Finding]:
    """Synthesize findings from historical data.

    Basic implementation processes historical patterns and creates findings.
    Future: Enhance with synthesis-master agent for deeper AI-powered analysis.

    Args:
        issue_data: Current issue data from Linear
        similar_issues: Similar issues from LinearHistoryResearcher
        pattern_matches: Pattern matches from LearningStore
        logger: Logger instance

    Returns:
        List of Finding objects with citations
    """
    from orchestrator.models import Citation

    findings = []

    # Finding 1: Similar issues analysis
    if similar_issues:
        resolved_count = sum(1 for issue in similar_issues if issue.get("state") == "completed")
        total_count = len(similar_issues)

        finding_text = f"Found {total_count} similar historical issues"
        if resolved_count > 0:
            finding_text += f", {resolved_count} of which were successfully resolved"
        finding_text += ". Review these for potential solutions."

        # Citation from first similar issue
        first_issue = similar_issues[0]
        citation = Citation(
            source_type="linear_issue",
            source_id=first_issue["id"],
            source_url=first_issue.get("url", f"https://linear.app/issue/{first_issue['id']}"),
            excerpt=first_issue.get("title", "Similar issue"),
        )

        findings.append(
            Finding(
                finding=finding_text,
                confidence="high",
                citations=[citation],
            )
        )

    # Finding 2: Resolution patterns analysis
    if pattern_matches:
        top_pattern = pattern_matches[0]  # Most confident pattern
        pattern_text = top_pattern.description
        pattern_confidence = top_pattern.confidence

        citation = Citation(
            source_type="pattern",
            source_id="pattern_store",
            source_url="",
            excerpt=f"Pattern: {pattern_text} (confidence: {pattern_confidence:.2f})",
        )

        findings.append(
            Finding(
                finding=f"Historical pattern identified: {pattern_text}",
                confidence="high" if pattern_confidence > 0.8 else "medium",
                citations=[citation],
            )
        )

    # If no historical data, create basic finding
    if not findings:
        citation = Citation(
            source_type="linear_issue",
            source_id=issue_data["id"],
            source_url=f"https://linear.app/issue/{issue_data['id']}",
            excerpt=issue_data.get("title", "Current issue"),
        )

        findings.append(
            Finding(
                finding="No similar historical issues found. This appears to be a new issue type.",
                confidence="medium",
                citations=[citation],
            )
        )

    logger.info(f"Generated {len(findings)} findings from historical data")
    return findings


def _generate_recommendations(
    issue_data: dict[str, Any],
    findings: list[Finding],
    pattern_matches: list[PatternMatch],
    logger: logging.Logger,
) -> list[Recommendation]:
    """Generate recommendations from findings.

    Basic implementation creates actionable recommendations from patterns.
    Future: Enhance with synthesis-master agent for AI-powered recommendations.

    Args:
        issue_data: Current issue data from Linear
        findings: Findings from _synthesize_findings
        pattern_matches: Pattern matches from LearningStore
        logger: Logger instance

    Returns:
        List of Recommendation objects with citations
    """
    from orchestrator.models import Citation

    recommendations = []

    # Recommendation based on patterns
    if pattern_matches:
        top_pattern = pattern_matches[0]
        pattern_text = top_pattern.description
        success_rate = top_pattern.successful_resolutions

        citation = Citation(
            source_type="pattern",
            source_id="pattern_store",
            source_url="",
            excerpt=f"Pattern successfully applied {success_rate} times: {pattern_text}",
        )

        confidence = "high" if top_pattern.confidence > 0.8 else "medium"
        recommendations.append(
            Recommendation(
                recommendation=f"Apply proven resolution pattern: {pattern_text}",
                reasoning=f"This approach has been successful in {success_rate} similar cases",
                confidence=confidence,
                citations=[citation],
            )
        )

    # Recommendation based on findings
    for finding in findings:
        # Only recommend review if we actually found similar issues (not "no similar issues")
        if (
            "similar historical issues" in finding.finding.lower()
            and "no similar" not in finding.finding.lower()
            and finding.citations
        ):
            # Recommend reviewing similar issues
            citation = finding.citations[0]

            recommendations.append(
                Recommendation(
                    recommendation="Review similar resolved issues for solution patterns",
                    reasoning="Historical data shows this issue type has known solutions",
                    confidence="medium",
                    citations=[citation],
                )
            )

    # If no specific recommendations, provide general guidance
    if not recommendations:
        citation = Citation(
            source_type="linear_issue",
            source_id=issue_data["id"],
            source_url=f"https://linear.app/issue/{issue_data['id']}",
            excerpt="Standard investigation recommended for new issue types",
        )

        recommendations.append(
            Recommendation(
                recommendation="Conduct detailed technical investigation",
                reasoning="No historical precedent found - requires manual analysis",
                confidence="medium",
                citations=[citation],
            )
        )

    logger.info(f"Generated {len(recommendations)} recommendations from findings")
    return recommendations


def _save_investigation(result: InvestigationResult, logger: logging.Logger) -> None:
    """Save investigation result to markdown file.

    Args:
        result: InvestigationResult to save
        logger: Logger instance

    Output Path:
        investigation_results/{issue_id}.md

    Markdown Format:
        ## Investigation: {issue_id}

        **Issue**: [{issue_id}]({issue_url})

        ### Research Sources
        - Linear issue history
        - Pattern store

        ### Findings
        {formatted findings with citations}

        ### Recommendations
        {formatted recommendations with citations}

        ### Pattern Matches
        {formatted pattern matches}

        ---
        *Generated by Orchestrator Investigation*
        *Duration: {duration}s | Citations: {count} | Patterns: {count}*

    Implementation:
        1. Create output_dir = Path("investigation_results"), mkdir with parents=True, exist_ok=True
        2. Build markdown content with sections
        3. Use CitationTracker to format findings and recommendations
        4. Write to output_path = output_dir / f"{result.issue_id}.md"
        5. Log success

    Error Handling:
        - Let exceptions propagate (file I/O errors should be visible)
    """
    # Create output directory
    output_dir = Path("investigation_results")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build markdown content
    tracker = CitationTracker()
    content_parts = [
        f"## Investigation: {result.issue_id}\n",
        f"**Issue**: [{result.issue_id}]({result.issue_url})\n",
        "\n### Research Sources\n",
        "- Linear issue history\n",
        "- Pattern store\n",
    ]

    # Findings section
    content_parts.append("\n### Findings\n")
    if result.findings:
        for finding in result.findings:
            content_parts.append(f"- {finding.finding}\n")
            formatted = tracker.format_citations_list(finding.citations)
            content_parts.append(f"  {formatted}\n")
    else:
        content_parts.append("*No findings generated (AI agent integration pending)*\n")

    # Recommendations section
    content_parts.append("\n### Recommendations\n")
    if result.recommendations:
        for recommendation in result.recommendations:
            content_parts.append(f"- **{recommendation.recommendation}** (confidence: {recommendation.confidence})\n")
            content_parts.append(f"  - Rationale: {recommendation.reasoning}\n")
            formatted = tracker.format_citations_list(recommendation.citations)
            content_parts.append(f"  {formatted}\n")
    else:
        content_parts.append("*No recommendations generated (AI agent integration pending)*\n")

    # Pattern matches section
    content_parts.append("\n### Pattern Matches\n")
    if result.pattern_matches:
        for match in result.pattern_matches:
            content_parts.append(f"    - {match.description}\n")
            content_parts.append(f"      Confidence: {match.confidence:.2f}\n")
            content_parts.append(f"      Success Rate: {match.successful_resolutions}\n")
    else:
        content_parts.append("*No pattern matches found*\n")

    # Footer with metadata
    content_parts.extend(
        [
            "\n---\n",
            "*Generated by Orchestrator Investigation*\n",
            f"*Duration: {result.duration:.2f}s | ",
            f"Citations: {result.citations_count} | ",
            f"Patterns: {len(result.pattern_matches)}*\n",
        ]
    )

    # Write to file
    output_path = output_dir / f"{result.issue_id}.md"
    output_path.write_text("".join(content_parts), encoding="utf-8")

    logger.info(f"Investigation saved to {output_path}")
