"""Pattern learning and matching for investigation workflow."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from orchestrator.models import Citation, PatternMatch


class LearningStore:
    """File-based pattern learning store for investigation insights."""

    def __init__(self: "LearningStore", patterns_file: str = "data/patterns.jsonl") -> None:
        """Initialize learning store with patterns file.

        Args:
            patterns_file: Path to JSONL patterns file (default: data/patterns.jsonl)
        """
        self.patterns_file = Path(patterns_file)
        self._ensure_data_directory()

    def _ensure_data_directory(self: "LearningStore") -> None:
        """Ensure data directory exists for patterns file."""
        self.patterns_file.parent.mkdir(parents=True, exist_ok=True)

    def record_pattern(
        self: "LearningStore",
        issue_pattern: str,
        recommendation: str,
        citations: list[Citation],
        outcome: str | None = None,
    ) -> str:
        """Record a new pattern from an investigation.

        Args:
            issue_pattern: Description of the issue pattern
            recommendation: Recommendation given for this pattern
            citations: Citations supporting the pattern
            outcome: Resolution outcome (None if not yet resolved)

        Returns:
            Pattern ID (generated from timestamp + hash)
        """
        # Generate pattern ID
        timestamp = datetime.utcnow().isoformat()
        pattern_id = f"P-{hashlib.md5(f'{timestamp}{issue_pattern}'.encode()).hexdigest()[:8]}"

        # Create pattern record
        pattern = {
            "pattern_id": pattern_id,
            "issue_pattern": issue_pattern,
            "recommendation": recommendation,
            "citations": [
                {
                    "source_type": c.source_type,
                    "source_id": c.source_id,
                    "source_url": c.source_url,
                    "excerpt": c.excerpt,
                    "retrieved_at": c.retrieved_at,
                }
                for c in citations
            ],
            "outcome": outcome,
            "successful_resolutions": 1 if outcome == "resolved" else 0,
            "total_uses": 1,
            "confidence": 1.0 if outcome == "resolved" else 0.5,  # Start at 0.5 if unresolved
            "created_at": timestamp,
            "updated_at": timestamp,
        }

        # Append to JSONL file
        with open(self.patterns_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(pattern, ensure_ascii=False) + "\n")

        return pattern_id

    def find_matching_patterns(
        self: "LearningStore", issue_description: str, min_confidence: float = 0.7
    ) -> list[PatternMatch]:
        """Find patterns matching the issue description.

        Args:
            issue_description: Description of the current issue
            min_confidence: Minimum confidence threshold (default: 0.7)

        Returns:
            List of PatternMatch objects with confidence ≥ min_confidence
        """
        if not self.patterns_file.exists():
            return []

        matches: list[PatternMatch] = []

        # Read all patterns from JSONL
        with open(self.patterns_file, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                pattern = json.loads(line)

                # Simple text similarity (contains check)
                # More sophisticated similarity could be added later
                if (
                    issue_description.lower() in pattern["issue_pattern"].lower()
                    or pattern["issue_pattern"].lower() in issue_description.lower()
                ) and pattern["confidence"] >= min_confidence:
                    # Convert citations back to Citation objects
                    citations = [Citation(**c) for c in pattern.get("citations", [])]

                    matches.append(
                        PatternMatch(
                            pattern_id=pattern["pattern_id"],
                            description=pattern["issue_pattern"],
                            confidence=pattern["confidence"],
                            successful_resolutions=pattern["successful_resolutions"],
                            citations=citations,
                        )
                    )

        # Sort by confidence descending
        matches.sort(key=lambda m: m.confidence, reverse=True)
        return matches

    def update_outcome(self: "LearningStore", pattern_id: str, outcome: str) -> bool:
        """Update a pattern's outcome when issue is resolved.

        Args:
            pattern_id: Pattern ID to update
            outcome: Resolution outcome ("resolved" or "not_resolved")

        Returns:
            True if pattern was found and updated, False otherwise
        """
        if not self.patterns_file.exists():
            return False

        # Read all patterns
        patterns: list[dict[str, Any]] = []
        updated = False

        with open(self.patterns_file, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                pattern = json.loads(line)

                # Update matching pattern
                if pattern["pattern_id"] == pattern_id:
                    pattern["outcome"] = outcome
                    pattern["total_uses"] += 1

                    if outcome == "resolved":
                        pattern["successful_resolutions"] += 1

                    # Update confidence: successful_resolutions / total_uses
                    pattern["confidence"] = pattern["successful_resolutions"] / pattern["total_uses"]
                    pattern["updated_at"] = datetime.utcnow().isoformat()
                    updated = True

                patterns.append(pattern)

        if updated:
            # Rewrite entire file with updated pattern
            with open(self.patterns_file, "w", encoding="utf-8") as f:
                for pattern in patterns:
                    f.write(json.dumps(pattern, ensure_ascii=False) + "\n")

        return updated
