"""Tests for investigation workflow."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from orchestrator.investigation import execute_investigation
from orchestrator.models import Citation, InvestigationResult


class TestInvestigation:
    """Test investigation workflow."""

    @patch("orchestrator.investigation.LearningStore")
    @patch("orchestrator.investigation.LinearHistoryResearcher")
    @patch("orchestrator.investigation.fetch_issue")
    def test_execute_investigation_success(
        self: "TestInvestigation",
        mock_fetch_issue,
        mock_researcher_class,
        mock_store_class,
        tmp_path: Path,
    ) -> None:
        """Test successful investigation execution end-to-end."""
        mock_fetch_issue.return_value = {
            "id": "TEST-100",
            "title": "Database timeout",
            "description": "Connection times out after 30s",
            "state": {"name": "todo"},
        }

        mock_researcher = MagicMock()
        mock_researcher.find_similar_issues.return_value = [
            {
                "id": "TEST-100",
                "title": "Database timeout",
                "description": "Connection times out after 30s",
                "url": "https://linear.app/issue/TEST-100",
                "state": "todo",
                "labels": "",
            }
        ]
        mock_researcher.find_resolution_patterns.return_value = [
            {"pattern": "Resolved by restarting database", "count": 3, "example_issue_id": "TEST-50"}
        ]
        mock_researcher.find_team_expertise.return_value = []
        mock_researcher.extract_citations_from_issue.return_value = Citation(
            source_type="linear_issue",
            source_id="TEST-100",
            source_url="https://linear.app/issue/TEST-100",
            excerpt="Database timeout",
        )
        mock_researcher_class.return_value = mock_researcher

        mock_store = MagicMock()
        mock_store.find_matching_patterns.return_value = []
        mock_store_class.return_value = mock_store

        result = execute_investigation("TEST-100")

        assert isinstance(result, InvestigationResult)
        assert result.success is True
        assert result.issue_id == "TEST-100"
        # Now returns actual findings/recommendations from historical data
        assert len(result.findings) > 0
        assert len(result.recommendations) > 0
        assert result.pattern_matches == []

    @patch("orchestrator.investigation.fetch_issue")
    def test_execute_investigation_fetch_failure(
        self: "TestInvestigation",
        mock_fetch_issue,
        tmp_path: Path,
    ) -> None:
        """Test investigation when fetch_issue fails."""
        mock_fetch_issue.side_effect = RuntimeError("API error")

        result = execute_investigation("TEST-999")

        assert isinstance(result, InvestigationResult)
        assert result.success is False
        assert result.error is not None
        assert "API error" in result.error

    @patch("orchestrator.investigation.LearningStore")
    @patch("orchestrator.investigation.LinearHistoryResearcher")
    @patch("orchestrator.investigation.fetch_issue")
    def test_execute_investigation_researcher_failure(
        self: "TestInvestigation",
        mock_fetch_issue,
        mock_researcher_class,
        mock_store_class,
        tmp_path: Path,
    ) -> None:
        """Test investigation when LinearHistoryResearcher fails."""
        mock_fetch_issue.return_value = {
            "id": "TEST-200",
            "title": "Test issue",
            "description": "Test description",
            "state": {"name": "todo"},
        }

        mock_researcher = MagicMock()
        mock_researcher.find_similar_issues.side_effect = Exception("Research failed")
        mock_researcher_class.return_value = mock_researcher

        result = execute_investigation("TEST-200")

        assert isinstance(result, InvestigationResult)
        assert result.success is False
        assert result.error is not None
        assert "Research failed" in result.error

    @patch("orchestrator.investigation.LearningStore")
    @patch("orchestrator.investigation.LinearHistoryResearcher")
    @patch("orchestrator.investigation.fetch_issue")
    def test_execute_investigation_creates_markdown(
        self: "TestInvestigation",
        mock_fetch_issue,
        mock_researcher_class,
        mock_store_class,
        tmp_path: Path,
    ) -> None:
        """Test that investigation creates markdown output file."""
        mock_fetch_issue.return_value = {
            "id": "TEST-300",
            "title": "Test issue",
            "description": "Test description",
            "state": {"name": "todo"},
        }

        mock_researcher = MagicMock()
        mock_researcher.find_similar_issues.return_value = []
        mock_researcher.find_resolution_patterns.return_value = []
        mock_researcher.find_team_expertise.return_value = []
        mock_researcher_class.return_value = mock_researcher

        mock_store = MagicMock()
        mock_store.find_matching_patterns.return_value = []
        mock_store_class.return_value = mock_store

        result = execute_investigation("TEST-300")

        assert result.success is True

        output_file = Path("investigation_results") / "TEST-300.md"
        assert output_file.exists()

        content = output_file.read_text()
        assert "# Investigation: TEST-300" in content
        assert "Test issue" in content

    @patch("orchestrator.investigation.LearningStore")
    @patch("orchestrator.investigation.LinearHistoryResearcher")
    @patch("orchestrator.investigation.fetch_issue")
    def test_execute_investigation_with_similar_issues(
        self: "TestInvestigation",
        mock_fetch_issue,
        mock_researcher_class,
        mock_store_class,
        tmp_path: Path,
    ) -> None:
        """Test investigation with multiple similar issues found."""
        mock_fetch_issue.return_value = {
            "id": "TEST-400",
            "title": "Database timeout",
            "description": "Connection times out",
            "state": {"name": "todo"},
        }

        mock_researcher = MagicMock()
        mock_researcher.find_similar_issues.return_value = [
            {
                "id": "TEST-400",
                "title": "Database timeout",
                "description": "Connection times out",
                "url": "https://linear.app/issue/TEST-400",
                "state": "todo",
                "labels": "",
            },
            {
                "id": "TEST-401",
                "title": "Database timeout again",
                "description": "Same issue",
                "url": "https://linear.app/issue/TEST-401",
                "state": "completed",
                "labels": "bug",
            },
        ]
        mock_researcher.find_resolution_patterns.return_value = []
        mock_researcher.find_team_expertise.return_value = []
        mock_researcher_class.return_value = mock_researcher

        mock_store = MagicMock()
        mock_store.find_matching_patterns.return_value = []
        mock_store_class.return_value = mock_store

        result = execute_investigation("TEST-400")

        assert result.success is True
        # Now returns actual findings from historical data
        assert len(result.findings) > 0
        assert result.similar_issues_count == 2  # Similar issues were found

    @patch("orchestrator.investigation.LearningStore")
    @patch("orchestrator.investigation.LinearHistoryResearcher")
    @patch("orchestrator.investigation.fetch_issue")
    def test_execute_investigation_with_patterns(
        self: "TestInvestigation",
        mock_fetch_issue,
        mock_researcher_class,
        mock_store_class,
        tmp_path: Path,
    ) -> None:
        """Test investigation with resolution patterns found."""
        mock_fetch_issue.return_value = {
            "id": "TEST-500",
            "title": "Memory leak",
            "description": "Service crashes",
            "state": {"name": "todo"},
        }

        mock_researcher = MagicMock()
        mock_researcher.find_similar_issues.return_value = []
        mock_researcher.find_resolution_patterns.return_value = [
            {"pattern": "Restart service", "count": 5, "example_issue_id": "TEST-450"},
            {"pattern": "Increase memory", "count": 2, "example_issue_id": "TEST-451"},
        ]
        mock_researcher.find_team_expertise.return_value = []
        mock_researcher_class.return_value = mock_researcher

        mock_store = MagicMock()
        mock_store.find_matching_patterns.return_value = []
        mock_store_class.return_value = mock_store

        result = execute_investigation("TEST-500")

        assert result.success is True
        # Now returns actual recommendations (no patterns, so basic recommendation)
        assert len(result.recommendations) > 0

    @patch("orchestrator.investigation.LearningStore")
    @patch("orchestrator.investigation.LinearHistoryResearcher")
    @patch("orchestrator.investigation.fetch_issue")
    def test_execute_investigation_no_historical_data(
        self: "TestInvestigation",
        mock_fetch_issue,
        mock_researcher_class,
        mock_store_class,
        tmp_path: Path,
    ) -> None:
        """Test that _synthesize_findings returns basic finding when no historical data."""
        mock_fetch_issue.return_value = {
            "id": "TEST-600",
            "title": "Test issue",
            "description": "Test description",
            "state": {"name": "todo"},
        }

        mock_researcher = MagicMock()
        mock_researcher.find_similar_issues.return_value = []
        mock_researcher.find_resolution_patterns.return_value = []
        mock_researcher.find_team_expertise.return_value = []
        mock_researcher_class.return_value = mock_researcher

        mock_store = MagicMock()
        mock_store.find_matching_patterns.return_value = []
        mock_store_class.return_value = mock_store

        result = execute_investigation("TEST-600")

        assert result.success is True
        assert len(result.findings) == 1
        assert "No similar historical issues found" in result.findings[0].finding

    @patch("orchestrator.investigation.LearningStore")
    @patch("orchestrator.investigation.LinearHistoryResearcher")
    @patch("orchestrator.investigation.fetch_issue")
    def test_execute_investigation_basic_recommendations(
        self: "TestInvestigation",
        mock_fetch_issue,
        mock_researcher_class,
        mock_store_class,
        tmp_path: Path,
    ) -> None:
        """Test that _generate_recommendations returns basic recommendation without historical data."""
        mock_fetch_issue.return_value = {
            "id": "TEST-700",
            "title": "Test issue",
            "description": "Test description",
            "state": {"name": "todo"},
        }

        mock_researcher = MagicMock()
        mock_researcher.find_similar_issues.return_value = []
        mock_researcher.find_resolution_patterns.return_value = []
        mock_researcher.find_team_expertise.return_value = []
        mock_researcher_class.return_value = mock_researcher

        mock_store = MagicMock()
        mock_store.find_matching_patterns.return_value = []
        mock_store_class.return_value = mock_store

        result = execute_investigation("TEST-700")

        assert result.success is True
        assert len(result.recommendations) == 1
        assert "Conduct detailed technical investigation" in result.recommendations[0].recommendation

    @patch("orchestrator.investigation.LearningStore")
    @patch("orchestrator.investigation.LinearHistoryResearcher")
    @patch("orchestrator.investigation.fetch_issue")
    def test_execute_investigation_markdown_content(
        self: "TestInvestigation",
        mock_fetch_issue,
        mock_researcher_class,
        mock_store_class,
        tmp_path: Path,
    ) -> None:
        """Test markdown file contains expected sections."""
        mock_fetch_issue.return_value = {
            "id": "TEST-800",
            "title": "Database timeout",
            "description": "Connection fails after 30s",
            "state": {"name": "in_progress"},
        }

        mock_researcher = MagicMock()
        mock_researcher.find_similar_issues.return_value = [
            {
                "id": "TEST-800",
                "title": "Database timeout",
                "description": "Connection fails",
                "url": "https://linear.app/issue/TEST-800",
                "state": "in_progress",
                "labels": "bug",
            }
        ]
        mock_researcher.find_resolution_patterns.return_value = [
            {"pattern": "Increase timeout", "count": 3, "example_issue_id": "TEST-750"}
        ]
        mock_researcher.find_team_expertise.return_value = []
        mock_researcher_class.return_value = mock_researcher

        mock_store = MagicMock()
        mock_store.find_matching_patterns.return_value = []
        mock_store_class.return_value = mock_store

        result = execute_investigation("TEST-800")

        assert result.success is True

        output_file = Path("investigation_results") / "TEST-800.md"
        content = output_file.read_text()

        # Check for generated content sections
        assert "TEST-800" in content
        assert "### Findings" in content
        assert "### Recommendations" in content
        assert "Database timeout" in content

    @patch("orchestrator.investigation.LearningStore")
    @patch("orchestrator.investigation.LinearHistoryResearcher")
    @patch("orchestrator.investigation.fetch_issue")
    def test_execute_investigation_result_validation(
        self: "TestInvestigation",
        mock_fetch_issue,
        mock_researcher_class,
        mock_store_class,
        tmp_path: Path,
    ) -> None:
        """Test that InvestigationResult passes Pydantic validation."""
        mock_fetch_issue.return_value = {
            "id": "TEST-900",
            "title": "Test issue",
            "description": "Test description",
            "state": {"name": "todo"},
        }

        mock_researcher = MagicMock()
        mock_researcher.find_similar_issues.return_value = []
        mock_researcher.find_resolution_patterns.return_value = []
        mock_researcher.find_team_expertise.return_value = []
        mock_researcher_class.return_value = mock_researcher

        mock_store = MagicMock()
        mock_store.find_matching_patterns.return_value = []
        mock_store_class.return_value = mock_store

        result = execute_investigation("TEST-900")

        assert isinstance(result, InvestigationResult)
        assert result.issue_id == "TEST-900"
        assert result.success is True
        assert isinstance(result.findings, list)
        assert isinstance(result.recommendations, list)
        assert isinstance(result.pattern_matches, list)
        assert isinstance(result.findings, list)
        assert isinstance(result.recommendations, list)
        assert result.error is None  # Success case has None, not empty string
