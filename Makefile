# Makefile for OpenCode Python
# Common commands for development and CI

.PHONY: help install dev test test-unit test-integration test-coverage lint lint-fix format clean build docs serve

# Default target
help:
	@echo "OpenCode Python - Available Commands"
	@echo "===================================="
	@echo ""
	@echo "Installation:"
	@echo "  make install        Install the package"
	@echo "  make dev            Install with development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test           Run all tests"
	@echo "  make test-unit      Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make test-coverage  Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           Run all linters"
	@echo "  make lint-fix       Run linters and fix issues"
	@echo "  make format         Format code with ruff"
	@echo "  make typecheck      Run mypy type checker"
	@echo ""
	@echo "Development:"
	@echo "  make clean          Clean generated files"
	@echo "  make build          Build the package"
	@echo "  make docs           Build documentation"
	@echo "  make serve          Start development server"
	@echo ""
	@echo "Pre-commit:"
	@echo "  make pre-commit     Run pre-commit on all files"
	@echo "  make pre-commit-install Install pre-commit hooks"

# Installation
install:
	cd src/opencode && pip install -e .

dev:
	cd src/opencode && pip install -e ".[dev]"

# Testing
test:
	cd src/opencode && pytest src/opencode/tests -v

test-unit:
	cd src/opencode && pytest src/opencode/tests/unit -v

test-integration:
	cd src/opencode && pytest src/opencode/tests/integration -v

test-coverage:
	cd src/opencode && pytest src/opencode/tests -v --cov=opencode --cov-report=html --cov-report=term

# Code Quality
lint:
	ruff check src/opencode/src/opencode
	mypy src/opencode/src/opencode --ignore-missing-imports

lint-fix:
	ruff check src/opencode/src/opencode --fix

format:
	ruff format src/opencode/src/opencode

format-check:
	ruff format src/opencode/src/opencode --check

typecheck:
	mypy src/opencode/src/opencode --ignore-missing-imports

# Development
clean:
	python scripts/clean.py --all

build:
	cd src/opencode && python -m build

docs:
	cd src/opencode && pdoc -o docs/html src/opencode

serve:
	cd src/opencode && python -m opencode serve

# Pre-commit
pre-commit-install:
	pre-commit install

pre-commit:
	pre-commit run --all-files

# Quick checks
check: lint format-check test-unit
	@echo "All checks passed!"

# Full CI pipeline
ci: install lint test-coverage
	@echo "CI pipeline completed!"