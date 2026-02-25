# Comprehensive Testing Plan for OpenCode Python

This document outlines a comprehensive testing strategy for the OpenCode Python project, designed to accommodate future changes and ensure reliability across all components.

**Current Status:** See [docs/TESTING_STATUS.md](../docs/TESTING_STATUS.md) for the latest test coverage and results.

> **Navigation:**
> - **Previous:** [CODE_IMPROVEMENT_PLAN.md](CODE_IMPROVEMENT_PLAN.md) - Code quality standards
> - **Next:** [USER_ACCEPTANCE_TESTING.md](USER_ACCEPTANCE_TESTING.md) - UAT validation

> **Related Documents:**
> - [README.md](../README.md) - Project overview and features
> - [MISSION.md](../MISSION.md) - Mission statement and core principles

---

## Definitions

### Complete Test Suite

A **complete test suite** is defined as:

1. **All test categories passing**: Unit, Integration, Provider, Prompt, Ollama, E2E, and Performance tests
2. **No skipped tests** (except those requiring unavailable external services like Ollama or API keys)
3. **No failing tests** - all tests must pass
4. **Minimum coverage threshold met**: At least 70% code coverage on non-excluded modules

### 100% Coverage

**100% coverage** means 100% of **non-excluded modules** are covered by tests. Modules listed in the Coverage Exclusions section below are not counted toward coverage calculations. This means:

- If excluded modules have 0% coverage, the project can still achieve 100% coverage
- Coverage reports should be interpreted as "coverage of testable code"
- The goal is meaningful test coverage, not arbitrary percentages on thin API wrappers

---

## Coverage Exclusions

The following modules are **excluded from coverage requirements** as they are thin wrappers around external APIs:

- All provider implementations in `provider/` (except `base.py`)
- These require complex HTTP mocking with limited testing value
- Focus provider testing on `provider/base.py` (currently at 90% coverage)

---

## Executive Summary

The testing strategy follows a multi-layered approach:
1. **Unit Tests** - Fast, isolated tests for individual components
2. **Integration Tests** - Tests for component interactions
3. **Provider Tests** - AI model provider testing with mock and real backends
4. **Prompt Evaluation Tests** - Compare prompts across different AI models
5. **Ollama Integration Tests** - Local LLM testing for accuracy and troubleshooting
6. **End-to-End Tests** - Full workflow testing
7. **Performance Tests** - Benchmark critical paths

---

## Detailed Testing Documentation

The following detailed documentation has been extracted to the `docs/` folder for easier maintenance and discoverability:

### Testing Infrastructure

| Document | Description |
|----------|-------------|
| [TESTING_INFRASTRUCTURE.md](../docs/TESTING_INFRASTRUCTURE.md) | Test directory structure and `conftest.py` configuration |
| [CI_CD_TESTING.md](../docs/CI_CD_TESTING.md) | pytest configuration and GitHub Actions workflows |
| [TEST_MAINTENANCE_GUIDE.md](../docs/TEST_MAINTENANCE_GUIDE.md) | Guidelines for adding and maintaining tests |

### Specialized Testing

| Document | Description |
|----------|-------------|
| [PROMPT_TESTING.md](../docs/PROMPT_TESTING.md) | Cross-model prompt comparison and accuracy benchmarks |
| [OLLAMA_TESTING.md](../docs/OLLAMA_TESTING.md) | Ollama integration, accuracy, and troubleshooting tests |
| [TEST_DISCOVERY.md](../docs/TEST_DISCOVERY.md) | Test discovery commands for new code and features |

---

## Summary

This testing plan provides:

1. **Comprehensive Coverage**: Unit, integration, provider, prompt, and E2E tests
2. **Prompt Comparison**: Cross-model comparison tests for prompt evaluation
3. **Ollama Testing**: Dedicated tests for Ollama integration, accuracy, and troubleshooting
4. **Future-Proof Design**: Modular structure that accommodates new features
5. **CI/CD Ready**: GitHub Actions workflow for automated testing
6. **Monitoring**: Accuracy tracking and metrics collection

---

## Quick Reference Commands

```bash
# Full test suite with coverage
cd src/opencode && python -m pytest src/opencode/tests/ --cov=src/opencode --cov-report=term-missing -q

# Quick test run (unit tests only)
cd src/opencode && python -m pytest src/opencode/tests/unit/ -v --tb=short

# Run specific test category
cd src/opencode && python -m pytest src/opencode/tests/integration/ -v
cd src/opencode && python -m pytest src/opencode/tests/providers/ -v

# Run with markers
cd src/opencode && python -m pytest -m "not slow" -v
cd src/opencode && python -m pytest -m "ollama" -v

# Generate HTML coverage report
cd src/opencode && python -m pytest --cov=src/opencode --cov-report=html
```

### Test Priority Matrix

| Priority | Test Type | Frequency | Automation |
|----------|-----------|-----------|------------|
| P0 | Unit Tests | Every commit | Full |
| P0 | Provider Tests | Every commit | Full (mock) |
| P1 | Integration Tests | Every PR | Full |
| P1 | Ollama Tests | Every PR | Full |
| P2 | Prompt Comparison | Weekly | Partial |
| P2 | Accuracy Benchmarks | Weekly | Full |
| P3 | E2E Tests | Release | Manual trigger |
