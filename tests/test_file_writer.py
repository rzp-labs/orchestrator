"""Tests for file writer module."""

from pathlib import Path

from orchestrator.file_writer import save_analysis


class TestSaveAnalysis:
    """Test save_analysis() function."""

    def test_creates_directory(self, tmp_path: Path) -> None:
        """Creates output directory if it doesn't exist."""
        output_dir = tmp_path / "results"
        assert not output_dir.exists()

        save_analysis(
            ticket_id="SP-123",
            comment="Test analysis",
            writes_enabled=False,
            output_dir=output_dir,
        )

        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_saves_file_with_correct_name(self, tmp_path: Path) -> None:
        """Saves file with ticket ID as name."""
        file_path = save_analysis(
            ticket_id="SP-456",
            comment="Test",
            writes_enabled=False,
            output_dir=tmp_path,
        )

        assert file_path.name == "SP-456.md"
        assert file_path.exists()

    def test_includes_comment_in_file(self, tmp_path: Path) -> None:
        """File contains the analysis comment."""
        comment = "## Test Analysis\nThis is a test."
        file_path = save_analysis(
            ticket_id="SP-789",
            comment=comment,
            writes_enabled=False,
            output_dir=tmp_path,
        )

        content = file_path.read_text()
        assert "## Test Analysis" in content
        assert "This is a test." in content

    def test_includes_metadata_footer(self, tmp_path: Path) -> None:
        """File includes metadata footer with timestamp and mode."""
        file_path = save_analysis(
            ticket_id="SP-999",
            comment="Test",
            writes_enabled=True,
            output_dir=tmp_path,
        )

        content = file_path.read_text()
        assert "---" in content
        assert "_Analysis generated:" in content
        assert "UTC_" in content
        assert "_Linear writes: enabled_" in content

    def test_overwrites_existing_file(self, tmp_path: Path) -> None:
        """Overwrites existing file for same ticket ID."""
        # First save
        save_analysis(
            ticket_id="SP-111",
            comment="First version",
            writes_enabled=False,
            output_dir=tmp_path,
        )

        # Second save
        file_path = save_analysis(
            ticket_id="SP-111",
            comment="Second version",
            writes_enabled=False,
            output_dir=tmp_path,
        )

        content = file_path.read_text()
        assert "Second version" in content
        assert "First version" not in content
