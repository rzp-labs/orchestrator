.PHONY: install check test test-cov format-sh check-sh clean help

# Ensure we use the local .venv, not parent workspace
SHELL := /bin/bash
export VIRTUAL_ENV :=
export UV_PROJECT_ENVIRONMENT := .venv

# Default target
help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies via uv"
	@echo "  make check      - Run linting and type checking"
	@echo "  make test       - Run tests"
	@echo "  make test-cov   - Run tests with coverage"
	@echo "  make format-sh  - Format shell scripts"
	@echo "  make check-sh   - Check shell script formatting"
	@echo "  make clean      - Remove build artifacts"

# Install dependencies
install:
	uv sync --all-extras

# Run linting and type checking
check:
	uv run ruff check src/ tests/
	uv run pyright src/ tests/

# Run tests with coverage (default includes coverage to maintain quality)
test:
	uv run pytest tests/ --cov=src --cov-report=term-missing

# Alias for test (kept for compatibility)
test-cov: test

# Format shell scripts
format-sh:
	pnpm exec shfmt -i 4 -w scripts/*.sh

# Check shell script formatting
check-sh:
	pnpm exec shfmt -d scripts/*.sh

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
