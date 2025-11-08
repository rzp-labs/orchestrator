"""Tests for Linear history research."""

from unittest.mock import patch

from orchestrator.linear_history import LinearHistoryResearcher
from orchestrator.models import Citation


class TestLinearHistoryResearcher:
    """Test LinearHistoryResearcher class."""

    @patch("orchestrator.linear_history.fetch_issue")
    def test_find_similar_issues_returns_current_issue(self: "TestLinearHistoryResearcher", mock_fetch_issue) -> None:
        """Test that find_similar_issues returns at least the current issue."""
        mock_fetch_issue.return_value = {
            "id": "ABC-123",
            "title": "Database timeout",
            "description": "Connection timeout after 30s",
            "state": {"name": "completed"},
        }

        researcher = LinearHistoryResearcher()
        results = researcher.find_similar_issues("ABC-123", max_results=50)

        assert len(results) >= 1
        assert results[0]["id"] == "ABC-123"
        assert results[0]["title"][:200] == "Database timeout"

    @patch("orchestrator.linear_history.fetch_issue")
    def test_find_similar_issues_respects_max_results(self: "TestLinearHistoryResearcher", mock_fetch_issue) -> None:
        """Test that find_similar_issues respects max_results parameter."""
        mock_fetch_issue.return_value = {
            "id": "ABC-456",
            "title": "Test issue",
            "description": "Test description",
            "state": {"name": "in_progress"},
        }

        researcher = LinearHistoryResearcher()
        results = researcher.find_similar_issues("ABC-456", max_results=10)

        assert len(results) <= 10

    @patch("orchestrator.linear_history.fetch_issue")
    def test_find_similar_issues_truncates_title(self: "TestLinearHistoryResearcher", mock_fetch_issue) -> None:
        """Test that long titles are truncated to 200 chars."""
        long_title = "X" * 300
        mock_fetch_issue.return_value = {
            "id": "ABC-789",
            "title": long_title,
            "description": "Short description",
            "state": {"name": "todo"},
        }

        researcher = LinearHistoryResearcher()
        results = researcher.find_similar_issues("ABC-789")

        assert len(results[0]["title"]) == 200

    @patch("orchestrator.linear_history.fetch_issue")
    def test_find_similar_issues_truncates_description(self: "TestLinearHistoryResearcher", mock_fetch_issue) -> None:
        """Test that long descriptions are truncated to 200 chars."""
        long_desc = "Y" * 300
        mock_fetch_issue.return_value = {
            "id": "ABC-999",
            "title": "Short title",
            "description": long_desc,
            "state": {"name": "done"},
        }

        researcher = LinearHistoryResearcher()
        results = researcher.find_similar_issues("ABC-999")

        assert len(results[0]["description"]) == 200

    @patch("orchestrator.linear_history.fetch_issue")
    def test_find_similar_issues_constructs_url(self: "TestLinearHistoryResearcher", mock_fetch_issue) -> None:
        """Test that Linear URL is constructed correctly."""
        mock_fetch_issue.return_value = {
            "id": "TEST-100",
            "title": "URL test",
            "description": "Testing URL construction",
            "state": {"name": "completed"},
        }

        researcher = LinearHistoryResearcher()
        results = researcher.find_similar_issues("TEST-100")

        assert results[0]["url"] == "https://linear.app/issue/TEST-100"

    @patch("orchestrator.linear_history.fetch_issue")
    def test_find_similar_issues_extracts_state(self: "TestLinearHistoryResearcher", mock_fetch_issue) -> None:
        """Test that issue state is extracted correctly."""
        mock_fetch_issue.return_value = {
            "id": "STATE-1",
            "title": "State test",
            "description": "Testing state extraction",
            "state": {"name": "in_progress"},
        }

        researcher = LinearHistoryResearcher()
        results = researcher.find_similar_issues("STATE-1")

        assert results[0]["state"] == "in_progress"

    @patch("orchestrator.linear_history.fetch_issue")
    def test_find_similar_issues_handles_missing_state(self: "TestLinearHistoryResearcher", mock_fetch_issue) -> None:
        """Test handling when state is missing from issue data."""
        mock_fetch_issue.return_value = {
            "id": "NO-STATE",
            "title": "Missing state",
            "description": "No state field",
            "state": {},
        }

        researcher = LinearHistoryResearcher()
        results = researcher.find_similar_issues("NO-STATE")

        assert results[0]["state"] == "unknown"

    @patch("orchestrator.linear_history.fetch_issue")
    def test_find_similar_issues_empty_labels_field(self: "TestLinearHistoryResearcher", mock_fetch_issue) -> None:
        """Test that labels field is initialized empty."""
        mock_fetch_issue.return_value = {
            "id": "NO-LABELS",
            "title": "No labels",
            "description": "Testing empty labels",
            "state": {"name": "todo"},
        }

        researcher = LinearHistoryResearcher()
        results = researcher.find_similar_issues("NO-LABELS")

        assert results[0]["labels"] == ""

    def test_extract_citations_from_issue_basic(self: "TestLinearHistoryResearcher") -> None:
        """Test extracting citation from basic issue."""
        researcher = LinearHistoryResearcher()

        issue = {
            "id": "ABC-200",
            "url": "https://linear.app/issue/ABC-200",
            "title": "Database connection timeout",
            "description": "Service fails to connect to database after 30 seconds",
        }

        citation = researcher.extract_citations_from_issue(issue)

        assert isinstance(citation, Citation)
        assert citation.source_type == "linear_issue"
        assert citation.source_id == "ABC-200"
        assert citation.source_url == "https://linear.app/issue/ABC-200"
        assert "Database connection timeout" in citation.excerpt

    def test_extract_citations_from_issue_includes_description(
        self: "TestLinearHistoryResearcher",
    ) -> None:
        """Test that citation includes first sentence of description."""
        researcher = LinearHistoryResearcher()

        issue = {
            "id": "ABC-300",
            "url": "https://linear.app/issue/ABC-300",
            "title": "Memory leak",
            "description": "Service memory grows over time. Restart required daily.",
        }

        citation = researcher.extract_citations_from_issue(issue)

        assert "Memory leak" in citation.excerpt
        assert "Service memory grows over time" in citation.excerpt

    def test_extract_citations_from_issue_truncates_long_excerpt(
        self: "TestLinearHistoryResearcher",
    ) -> None:
        """Test that long title and description are truncated to 200 chars total."""
        researcher = LinearHistoryResearcher()

        long_title = "A" * 150  # Long title
        short_desc = "B" * 100  # Short enough to be added (< 150 char condition)
        issue = {
            "id": "ABC-400",
            "url": "https://linear.app/issue/ABC-400",
            "title": long_title,
            "description": short_desc,  # Short enough to be included
        }

        citation = researcher.extract_citations_from_issue(issue)

        # Implementation combines title (150) + ": " (2) + desc (100) = 252, truncated to 200
        assert len(citation.excerpt) == 200
        assert citation.excerpt.startswith("A")  # Title is present
        assert ": B" in citation.excerpt  # Description was added

    def test_extract_citations_from_issue_handles_missing_description(
        self: "TestLinearHistoryResearcher",
    ) -> None:
        """Test citation when description is missing."""
        researcher = LinearHistoryResearcher()

        issue = {
            "id": "ABC-500",
            "url": "https://linear.app/issue/ABC-500",
            "title": "Only title",
        }

        citation = researcher.extract_citations_from_issue(issue)

        assert citation.excerpt == "Only title"

    def test_extract_citations_from_issue_handles_empty_description(
        self: "TestLinearHistoryResearcher",
    ) -> None:
        """Test citation when description is empty string."""
        researcher = LinearHistoryResearcher()

        issue = {
            "id": "ABC-600",
            "url": "https://linear.app/issue/ABC-600",
            "title": "Title only again",
            "description": "",
        }

        citation = researcher.extract_citations_from_issue(issue)

        assert citation.excerpt == "Title only again"

    def test_find_resolution_patterns_empty_list(self: "TestLinearHistoryResearcher") -> None:
        """Test finding patterns with empty issue list."""
        researcher = LinearHistoryResearcher()

        patterns = researcher.find_resolution_patterns([])

        assert len(patterns) == 0

    def test_find_resolution_patterns_groups_by_state(self: "TestLinearHistoryResearcher") -> None:
        """Test that patterns are grouped by resolution state."""
        researcher = LinearHistoryResearcher()

        similar_issues = [
            {"id": "A-1", "state": "completed"},
            {"id": "A-2", "state": "completed"},
            {"id": "A-3", "state": "done"},
        ]

        patterns = researcher.find_resolution_patterns(similar_issues)

        assert len(patterns) == 2
        # Find completed pattern
        completed_pattern = next(p for p in patterns if "completed" in p["pattern"])
        assert completed_pattern["count"] == 2

    def test_find_resolution_patterns_counts_occurrences(
        self: "TestLinearHistoryResearcher",
    ) -> None:
        """Test that pattern counts are accurate."""
        researcher = LinearHistoryResearcher()

        similar_issues = [
            {"id": "B-1", "state": "completed"},
            {"id": "B-2", "state": "completed"},
            {"id": "B-3", "state": "completed"},
            {"id": "B-4", "state": "in_progress"},
        ]

        patterns = researcher.find_resolution_patterns(similar_issues)

        completed = next(p for p in patterns if "completed" in p["pattern"])
        assert completed["count"] == 3

    def test_find_resolution_patterns_includes_example_issue(
        self: "TestLinearHistoryResearcher",
    ) -> None:
        """Test that patterns include example issue ID."""
        researcher = LinearHistoryResearcher()

        similar_issues = [
            {"id": "C-100", "state": "done"},
            {"id": "C-200", "state": "done"},
        ]

        patterns = researcher.find_resolution_patterns(similar_issues)

        assert len(patterns) == 1
        assert patterns[0]["example_issue_id"] in ["C-100", "C-200"]

    def test_find_resolution_patterns_sorted_by_count(
        self: "TestLinearHistoryResearcher",
    ) -> None:
        """Test that patterns are sorted by count descending."""
        researcher = LinearHistoryResearcher()

        similar_issues = [
            {"id": "D-1", "state": "completed"},
            {"id": "D-2", "state": "done"},
            {"id": "D-3", "state": "done"},
            {"id": "D-4", "state": "done"},
        ]

        patterns = researcher.find_resolution_patterns(similar_issues)

        assert len(patterns) == 2
        assert patterns[0]["count"] == 3  # "done" appears 3 times
        assert patterns[1]["count"] == 1  # "completed" appears 1 time

    def test_find_resolution_patterns_ignores_non_completed_states(
        self: "TestLinearHistoryResearcher",
    ) -> None:
        """Test that only completed/done/closed states are counted."""
        researcher = LinearHistoryResearcher()

        similar_issues = [
            {"id": "E-1", "state": "in_progress"},
            {"id": "E-2", "state": "todo"},
            {"id": "E-3", "state": "backlog"},
        ]

        patterns = researcher.find_resolution_patterns(similar_issues)

        assert len(patterns) == 0

    def test_find_team_expertise_returns_empty_list(self: "TestLinearHistoryResearcher") -> None:
        """Test that find_team_expertise returns empty list (current stub)."""
        researcher = LinearHistoryResearcher()

        similar_issues = [
            {"id": "F-1", "state": "completed"},
            {"id": "F-2", "state": "completed"},
        ]

        expertise = researcher.find_team_expertise(similar_issues)

        assert isinstance(expertise, list)
        assert len(expertise) == 0
