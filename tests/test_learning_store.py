"""Tests for pattern learning and matching."""

import json
from pathlib import Path

from orchestrator.learning_store import LearningStore
from orchestrator.models import Citation


class TestLearningStore:
    """Test LearningStore class."""

    def test_init_creates_data_directory(self: "TestLearningStore", tmp_path: Path) -> None:
        """Test that LearningStore creates data directory on init."""
        patterns_file = tmp_path / "patterns.jsonl"

        store = LearningStore(patterns_file=str(patterns_file))

        assert patterns_file.parent.exists()
        assert store.patterns_file == patterns_file

    def test_record_pattern_creates_file(self: "TestLearningStore", tmp_path: Path) -> None:
        """Test that record_pattern creates JSONL file."""
        patterns_file = tmp_path / "patterns.jsonl"
        store = LearningStore(patterns_file=str(patterns_file))

        citations = [
            Citation(
                source_type="linear_issue",
                source_id="ABC-100",
                source_url="https://linear.app/issue/ABC-100",
                excerpt="Similar issue",
            )
        ]

        pattern_id = store.record_pattern(
            issue_pattern="Database timeout errors",
            recommendation="Increase connection pool",
            citations=citations,
            outcome=None,
        )

        assert patterns_file.exists()
        assert pattern_id.startswith("P-")

    def test_record_pattern_writes_jsonl_format(self: "TestLearningStore", tmp_path: Path) -> None:
        """Test that record_pattern writes proper JSONL format."""
        patterns_file = tmp_path / "patterns.jsonl"
        store = LearningStore(patterns_file=str(patterns_file))

        citations = [
            Citation(
                source_type="linear_issue",
                source_id="ABC-200",
                source_url="https://linear.app/issue/ABC-200",
                excerpt="Test citation",
            )
        ]

        pattern_id = store.record_pattern(
            issue_pattern="Memory leak in service",
            recommendation="Restart service daily",
            citations=citations,
            outcome=None,
        )

        # Read and parse JSONL
        with open(patterns_file) as f:
            line = f.readline()
            pattern = json.loads(line)

        assert pattern["pattern_id"] == pattern_id
        assert pattern["issue_pattern"] == "Memory leak in service"
        assert pattern["recommendation"] == "Restart service daily"
        assert len(pattern["citations"]) == 1
        assert pattern["outcome"] is None
        assert pattern["successful_resolutions"] == 0
        assert pattern["total_uses"] == 1
        assert pattern["confidence"] == 0.5  # Unresolved starts at 0.5

    def test_record_pattern_with_resolved_outcome(self: "TestLearningStore", tmp_path: Path) -> None:
        """Test recording a pattern that was immediately resolved."""
        patterns_file = tmp_path / "patterns.jsonl"
        store = LearningStore(patterns_file=str(patterns_file))

        store.record_pattern(
            issue_pattern="CPU spike",
            recommendation="Kill rogue process",
            citations=[
                Citation(
                    source_type="logs",
                    source_id="log-123",
                    source_url="https://logs/123",
                    excerpt="Process X using 100% CPU",
                )
            ],
            outcome="resolved",
        )

        with open(patterns_file) as f:
            pattern = json.loads(f.readline())

        assert pattern["outcome"] == "resolved"
        assert pattern["successful_resolutions"] == 1
        assert pattern["total_uses"] == 1
        assert pattern["confidence"] == 1.0  # Resolved on first use = 100% confidence

    def test_find_matching_patterns_empty_file(self: "TestLearningStore", tmp_path: Path) -> None:
        """Test finding patterns when file doesn't exist."""
        patterns_file = tmp_path / "nonexistent.jsonl"
        store = LearningStore(patterns_file=str(patterns_file))

        matches = store.find_matching_patterns("database timeout", min_confidence=0.7)

        assert len(matches) == 0

    def test_find_matching_patterns_exact_match(self: "TestLearningStore", tmp_path: Path) -> None:
        """Test finding patterns with exact text match."""
        patterns_file = tmp_path / "patterns.jsonl"
        store = LearningStore(patterns_file=str(patterns_file))

        # Record a pattern
        citations = [
            Citation(
                source_type="linear_issue",
                source_id="ABC-300",
                source_url="https://linear.app/issue/ABC-300",
                excerpt="Fixed timeout",
            )
        ]
        store.record_pattern(
            issue_pattern="database connection timeout",
            recommendation="Increase pool size",
            citations=citations,
            outcome="resolved",
        )

        # Search for exact match
        matches = store.find_matching_patterns("database connection timeout", min_confidence=0.7)

        assert len(matches) == 1
        assert matches[0].description == "database connection timeout"
        assert matches[0].confidence == 1.0

    def test_find_matching_patterns_substring_match(self: "TestLearningStore", tmp_path: Path) -> None:
        """Test finding patterns with substring matching."""
        patterns_file = tmp_path / "patterns.jsonl"
        store = LearningStore(patterns_file=str(patterns_file))

        citations = [
            Citation(
                source_type="linear_issue",
                source_id="ABC-400",
                source_url="https://linear.app/issue/ABC-400",
                excerpt="Example",
            )
        ]
        store.record_pattern(
            issue_pattern="service crashes randomly",
            recommendation="Add error handling",
            citations=citations,
            outcome="resolved",
        )

        # Search with substring
        matches = store.find_matching_patterns("service crashes", min_confidence=0.7)

        assert len(matches) == 1
        assert "crashes" in matches[0].description

    def test_find_matching_patterns_filters_low_confidence(self: "TestLearningStore", tmp_path: Path) -> None:
        """Test that low-confidence patterns are filtered out."""
        patterns_file = tmp_path / "patterns.jsonl"
        store = LearningStore(patterns_file=str(patterns_file))

        citations = [
            Citation(
                source_type="pattern",
                source_id="P-1",
                source_url="https://internal/P-1",
                excerpt="Test",
            )
        ]

        # Record unresolved pattern (confidence 0.5)
        store.record_pattern(
            issue_pattern="unknown error occurs",
            recommendation="Check logs",
            citations=citations,
            outcome=None,
        )

        # Search with high confidence threshold
        matches = store.find_matching_patterns("unknown error occurs", min_confidence=0.7)

        assert len(matches) == 0  # 0.5 < 0.7, should be filtered

    def test_find_matching_patterns_sorts_by_confidence(self: "TestLearningStore", tmp_path: Path) -> None:
        """Test that results are sorted by confidence descending."""
        patterns_file = tmp_path / "patterns.jsonl"
        store = LearningStore(patterns_file=str(patterns_file))

        citations = [
            Citation(
                source_type="pattern",
                source_id="P-X",
                source_url="https://internal/P-X",
                excerpt="Test",
            )
        ]

        # Record pattern with low confidence
        store.record_pattern(
            issue_pattern="error type A",
            recommendation="Fix A",
            citations=citations,
            outcome=None,  # confidence = 0.5
        )

        # Record pattern with high confidence
        store.record_pattern(
            issue_pattern="error type A occurs",
            recommendation="Fix B",
            citations=citations,
            outcome="resolved",  # confidence = 1.0
        )

        matches = store.find_matching_patterns("error type A", min_confidence=0.3)

        assert len(matches) == 2
        assert matches[0].confidence == 1.0  # Higher confidence first
        assert matches[1].confidence == 0.5

    def test_update_outcome_pattern_not_found(self: "TestLearningStore", tmp_path: Path) -> None:
        """Test updating outcome when pattern doesn't exist."""
        patterns_file = tmp_path / "patterns.jsonl"
        store = LearningStore(patterns_file=str(patterns_file))

        updated = store.update_outcome("P-nonexistent", "resolved")

        assert updated is False

    def test_update_outcome_success(self: "TestLearningStore", tmp_path: Path) -> None:
        """Test successfully updating a pattern's outcome."""
        patterns_file = tmp_path / "patterns.jsonl"
        store = LearningStore(patterns_file=str(patterns_file))

        citations = [
            Citation(
                source_type="linear_issue",
                source_id="ABC-500",
                source_url="https://linear.app/issue/ABC-500",
                excerpt="Test",
            )
        ]

        # Record initial pattern
        pattern_id = store.record_pattern(
            issue_pattern="initial issue",
            recommendation="try something",
            citations=citations,
            outcome=None,
        )

        # Update outcome
        updated = store.update_outcome(pattern_id, "resolved")

        assert updated is True

        # Verify file was updated
        with open(patterns_file) as f:
            pattern = json.loads(f.readline())

        assert pattern["outcome"] == "resolved"
        assert pattern["successful_resolutions"] == 1
        assert pattern["total_uses"] == 2  # Incremented from 1 to 2
        assert pattern["confidence"] == 0.5  # 1 success / 2 uses

    def test_update_outcome_increments_uses(self: "TestLearningStore", tmp_path: Path) -> None:
        """Test that update_outcome increments total_uses."""
        patterns_file = tmp_path / "patterns.jsonl"
        store = LearningStore(patterns_file=str(patterns_file))

        citations = [
            Citation(
                source_type="pattern",
                source_id="P-Y",
                source_url="https://internal/P-Y",
                excerpt="Test",
            )
        ]

        pattern_id = store.record_pattern(
            issue_pattern="recurring bug",
            recommendation="apply patch",
            citations=citations,
            outcome="resolved",
        )

        # First update (not resolved)
        store.update_outcome(pattern_id, "not_resolved")

        with open(patterns_file) as f:
            pattern = json.loads(f.readline())

        assert pattern["total_uses"] == 2  # Was 1, now 2
        assert pattern["successful_resolutions"] == 1  # No change
        assert pattern["confidence"] == 0.5  # 1/2

    def test_update_outcome_recalculates_confidence(self: "TestLearningStore", tmp_path: Path) -> None:
        """Test that confidence is recalculated based on success rate."""
        patterns_file = tmp_path / "patterns.jsonl"
        store = LearningStore(patterns_file=str(patterns_file))

        citations = [
            Citation(
                source_type="pattern",
                source_id="P-Z",
                source_url="https://internal/P-Z",
                excerpt="Test",
            )
        ]

        pattern_id = store.record_pattern(
            issue_pattern="test pattern",
            recommendation="test fix",
            citations=citations,
            outcome="resolved",  # 1 success, 1 use, confidence=1.0
        )

        # Add more uses
        store.update_outcome(pattern_id, "resolved")  # 2 success, 2 uses, confidence=1.0
        store.update_outcome(pattern_id, "not_resolved")  # 2 success, 3 uses, confidence=0.67
        store.update_outcome(pattern_id, "not_resolved")  # 2 success, 4 uses, confidence=0.5

        with open(patterns_file) as f:
            pattern = json.loads(f.readline())

        assert pattern["successful_resolutions"] == 2
        assert pattern["total_uses"] == 4
        assert pattern["confidence"] == 0.5

    def test_record_multiple_patterns_appends_to_file(self: "TestLearningStore", tmp_path: Path) -> None:
        """Test that multiple patterns are appended to JSONL file."""
        patterns_file = tmp_path / "patterns.jsonl"
        store = LearningStore(patterns_file=str(patterns_file))

        citations = [
            Citation(
                source_type="pattern",
                source_id="P-MULTI",
                source_url="https://internal/P-MULTI",
                excerpt="Test",
            )
        ]

        # Record three patterns
        id1 = store.record_pattern("pattern 1", "fix 1", citations, None)
        id2 = store.record_pattern("pattern 2", "fix 2", citations, "resolved")
        id3 = store.record_pattern("pattern 3", "fix 3", citations, None)

        # Read all lines
        with open(patterns_file) as f:
            lines = f.readlines()

        assert len(lines) == 3
        assert json.loads(lines[0])["pattern_id"] == id1
        assert json.loads(lines[1])["pattern_id"] == id2
        assert json.loads(lines[2])["pattern_id"] == id3

    def test_find_matching_patterns_with_citations(self: "TestLearningStore", tmp_path: Path) -> None:
        """Test that found patterns include their citations."""
        patterns_file = tmp_path / "patterns.jsonl"
        store = LearningStore(patterns_file=str(patterns_file))

        citations = [
            Citation(
                source_type="linear_issue",
                source_id="ABC-600",
                source_url="https://linear.app/issue/ABC-600",
                excerpt="Original issue",
            ),
            Citation(
                source_type="git_commit",
                source_id="def456",
                source_url="https://github.com/repo/commit/def456",
                excerpt="Fix commit",
            ),
        ]

        store.record_pattern(
            issue_pattern="documented pattern with citations",
            recommendation="follow documented fix",
            citations=citations,
            outcome="resolved",
        )

        matches = store.find_matching_patterns("documented pattern", min_confidence=0.7)

        assert len(matches) == 1
        assert len(matches[0].citations) == 2
        assert matches[0].citations[0].source_id == "ABC-600"
        assert matches[0].citations[1].source_id == "def456"
