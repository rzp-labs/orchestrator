# Changelog

All notable changes to Orchestrator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release
- Support triage workflow
- Linear integration via linear-cli
- AI-powered validity and severity assessment
- Claude Code hooks for metrics collection
- Defensive utilities for LLM response handling

### Documentation
- Complete setup guide
- Workflow documentation
- Architecture documentation
- Adding workflows guide
- Hooks and skills documentation

## [0.1.0] - 2025-10-26

### Added
- Initial project structure
- Support triage workflow
- Linear CLI integration
- Agent delegation via Claude Code SDK
- Pydantic domain models
- Defensive utilities (parse_llm_json, retry_cli_command)
- Claude Code hooks for logging
- Comprehensive documentation
- Test infrastructure

### Developer Experience
- uv for dependency management
- ruff for linting/formatting
- pytest for testing
- pyright for type checking
- shfmt for shell script formatting
- Makefile for standard commands

[Unreleased]: https://github.com/rzp-labs/orchestrator/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/rzp-labs/orchestrator/releases/tag/v0.1.0
