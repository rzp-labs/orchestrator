# Changelog

All notable changes to Orchestrator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Investigation workflow for researching Linear issue history
- Linear history research module (`linear_history.py`)
- Citation tracking system (`citation_tracker.py`) with mandatory source validation
- Learning store (`learning_store.py`) for pattern recognition and recommendations
- Investigation models: `Citation`, `Finding`, `Recommendation`, `InvestigationResult`
- CLI command `orchestrator investigate <issue-id>`
- File-based pattern storage in JSONL format
- Automatic pattern learning from issue resolutions

### Changed
- Extended models.py with investigation-specific Pydantic models
- Enhanced CLI with investigation command group

## [0.1.0] - 2025-10-26

### Added
- Initial release
- Support triage workflow
- Linear integration via GraphQL API
- AI-powered validity and severity assessment
- Claude Code hooks for metrics collection
- Defensive utilities for LLM response handling
- Pydantic domain models
- Comprehensive documentation
- Test infrastructure

### Documentation
- Complete setup guide
- Workflow documentation
- Architecture documentation
- Adding workflows guide
- Hooks and skills documentation

### Developer Experience
- uv for dependency management
- ruff for linting/formatting
- pytest for testing
- pyright for type checking
- shfmt for shell script formatting
- Makefile for standard commands

[Unreleased]: https://github.com/rzp-labs/orchestrator/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/rzp-labs/orchestrator/releases/tag/v0.1.0
