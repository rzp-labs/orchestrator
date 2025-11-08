"""Tests for citation tracking and formatting."""

from orchestrator.citation_tracker import CitationTracker
from orchestrator.models import Citation, Finding, Recommendation


class TestCitationTracker:
    """Test CitationTracker class."""

    def test_add_citation_linear_issue(self: "TestCitationTracker") -> None:
        """Test adding a linear_issue citation to tracker."""
        tracker = CitationTracker()

        citation = Citation(
            source_type="linear_issue",
            source_id="ABC-123",
            source_url="https://linear.app/issue/ABC-123",
            excerpt="Sample issue excerpt",
        )

        tracker.add_citation(citation)

        assert len(tracker.citations) == 1
        assert tracker.citations[0].source_id == "ABC-123"
        assert tracker.citations[0].source_type == "linear_issue"

    def test_add_citation_git_commit(self: "TestCitationTracker") -> None:
        """Test adding a git_commit citation to tracker."""
        tracker = CitationTracker()

        citation = Citation(
            source_type="git_commit",
            source_id="abc123def",
            source_url="https://github.com/repo/commit/abc123def",
            excerpt="Fixed database connection timeout",
        )

        tracker.add_citation(citation)

        assert len(tracker.citations) == 1
        assert tracker.citations[0].source_type == "git_commit"

    def test_add_multiple_citations(self: "TestCitationTracker") -> None:
        """Test adding multiple citations to tracker."""
        tracker = CitationTracker()

        citations = [
            Citation(
                source_type="linear_issue",
                source_id="ABC-1",
                source_url="https://linear.app/issue/ABC-1",
                excerpt="First issue",
            ),
            Citation(
                source_type="codebase",
                source_id="file.py:42",
                source_url="https://github.com/repo/blob/main/file.py#L42",
                excerpt="Relevant code snippet",
            ),
            Citation(
                source_type="pattern",
                source_id="P-456",
                source_url="https://internal/pattern/P-456",
                excerpt="Known pattern",
            ),
        ]

        for citation in citations:
            tracker.add_citation(citation)

        assert len(tracker.citations) == 3
        assert tracker.get_total_citations() == 3

    def test_validate_finding_with_citations(self: "TestCitationTracker") -> None:
        """Test validating a finding that has citations."""
        tracker = CitationTracker()

        finding = Finding(
            finding="Database connection timeout observed",
            confidence="high",
            citations=[
                Citation(
                    source_type="linear_issue",
                    source_id="ABC-100",
                    source_url="https://linear.app/issue/ABC-100",
                    excerpt="Same error pattern",
                )
            ],
        )

        is_valid, error_msg = tracker.validate_finding(finding)

        assert is_valid is True
        assert error_msg == ""

    def test_validate_finding_without_citations(self: "TestCitationTracker") -> None:
        """Test validating a finding that lacks citations."""
        tracker = CitationTracker()

        # Create finding without citations (bypassing Pydantic for test)
        # Normally Pydantic would reject this, but we test the validation method directly
        finding_data = {
            "finding": "This is a very long finding that exceeds minimum length requirement",
            "confidence": "low",
            "citations": [],
        }
        # Bypass validation to test the validator
        finding = Finding.model_construct(**finding_data)

        is_valid, error_msg = tracker.validate_finding(finding)

        assert is_valid is False
        assert "has no citations" in error_msg
        assert "This is a very long finding that exceeds" in error_msg

    def test_validate_finding_truncates_long_text(self: "TestCitationTracker") -> None:
        """Test that validation error message truncates long finding text."""
        tracker = CitationTracker()

        long_finding_text = "X" * 100  # 100 character finding
        finding_data = {
            "finding": long_finding_text,
            "confidence": "medium",
            "citations": [],
        }
        finding = Finding.model_construct(**finding_data)

        is_valid, error_msg = tracker.validate_finding(finding)

        assert is_valid is False
        assert "..." in error_msg  # Should be truncated with ellipsis
        assert len(error_msg) < len(long_finding_text) + 50  # Should be shorter than full text

    def test_validate_recommendation_with_citations(self: "TestCitationTracker") -> None:
        """Test validating a recommendation that has citations."""
        tracker = CitationTracker()

        recommendation = Recommendation(
            recommendation="Increase connection pool size",
            reasoning="Similar issues resolved by pool tuning",
            confidence="high",
            citations=[
                Citation(
                    source_type="linear_issue",
                    source_id="ABC-200",
                    source_url="https://linear.app/issue/ABC-200",
                    excerpt="Pool size increased from 50 to 100",
                )
            ],
        )

        is_valid, error_msg = tracker.validate_recommendation(recommendation)

        assert is_valid is True
        assert error_msg == ""

    def test_validate_recommendation_without_citations(self: "TestCitationTracker") -> None:
        """Test validating a recommendation that lacks citations."""
        tracker = CitationTracker()

        recommendation_data = {
            "recommendation": "Do something important that is long enough",
            "reasoning": "Because reasons that are sufficiently detailed",
            "confidence": "low",
            "citations": [],
        }
        recommendation = Recommendation.model_construct(**recommendation_data)

        is_valid, error_msg = tracker.validate_recommendation(recommendation)

        assert is_valid is False
        assert "has no citations" in error_msg
        assert "Do something important" in error_msg

    def test_format_citation_linear_issue(self: "TestCitationTracker") -> None:
        """Test formatting a linear_issue citation as markdown."""
        tracker = CitationTracker()

        citation = Citation(
            source_type="linear_issue",
            source_id="ABC-123",
            source_url="https://linear.app/issue/ABC-123",
            excerpt="Database timeout error",
        )

        formatted = tracker.format_citation(citation)

        assert "linear_issue: ABC-123" in formatted
        assert "https://linear.app/issue/ABC-123" in formatted
        assert "Database timeout error" in formatted
        assert formatted.startswith("- [")
        assert "](" in formatted

    def test_format_citation_git_commit(self: "TestCitationTracker") -> None:
        """Test formatting a git_commit citation as markdown."""
        tracker = CitationTracker()

        citation = Citation(
            source_type="git_commit",
            source_id="abc123",
            source_url="https://github.com/repo/commit/abc123",
            excerpt="Fixed connection pool bug",
        )

        formatted = tracker.format_citation(citation)

        assert "git_commit: abc123" in formatted
        assert "https://github.com/repo/commit/abc123" in formatted
        assert "Fixed connection pool bug" in formatted

    def test_format_citations_list_empty(self: "TestCitationTracker") -> None:
        """Test formatting an empty citations list."""
        tracker = CitationTracker()

        formatted = tracker.format_citations_list([])

        assert formatted == "(No citations)"

    def test_format_citations_list_single(self: "TestCitationTracker") -> None:
        """Test formatting a single citation."""
        tracker = CitationTracker()

        citations = [
            Citation(
                source_type="linear_issue",
                source_id="ABC-100",
                source_url="https://linear.app/issue/ABC-100",
                excerpt="Example issue",
            )
        ]

        formatted = tracker.format_citations_list(citations)

        assert "**Supporting Evidence:**" in formatted
        assert "linear_issue: ABC-100" in formatted
        assert formatted.count("\n") >= 1  # Header + citation

    def test_format_citations_list_multiple(self: "TestCitationTracker") -> None:
        """Test formatting multiple citations."""
        tracker = CitationTracker()

        citations = [
            Citation(
                source_type="linear_issue",
                source_id="ABC-100",
                source_url="https://linear.app/issue/ABC-100",
                excerpt="First issue",
            ),
            Citation(
                source_type="linear_issue",
                source_id="ABC-200",
                source_url="https://linear.app/issue/ABC-200",
                excerpt="Second issue",
            ),
            Citation(
                source_type="git_commit",
                source_id="abc123",
                source_url="https://github.com/repo/commit/abc123",
                excerpt="Related commit",
            ),
        ]

        formatted = tracker.format_citations_list(citations)

        assert "**Supporting Evidence:**" in formatted
        assert "ABC-100" in formatted
        assert "ABC-200" in formatted
        assert "abc123" in formatted
        assert formatted.count("- [") == 3  # Three citation bullets

    def test_get_total_citations_empty(self: "TestCitationTracker") -> None:
        """Test getting citation count from empty tracker."""
        tracker = CitationTracker()

        assert tracker.get_total_citations() == 0

    def test_get_total_citations_after_additions(self: "TestCitationTracker") -> None:
        """Test getting citation count after adding citations."""
        tracker = CitationTracker()

        for i in range(5):
            citation = Citation(
                source_type="linear_issue",
                source_id=f"ABC-{i}",
                source_url=f"https://linear.app/issue/ABC-{i}",
                excerpt=f"Issue {i}",
            )
            tracker.add_citation(citation)

        assert tracker.get_total_citations() == 5
