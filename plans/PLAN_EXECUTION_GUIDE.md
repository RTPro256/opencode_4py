# Plan Execution Guide

This document provides concise execution steps for the project plans.

> **Navigation:**
> - **Previous:** [FOR_TESTING_UPDATE_PLAN.md](FOR_TESTING_UPDATE_PLAN.md) - TUI troubleshooting
> - **Next:** [PLAN_INDEX.md](PLAN_INDEX.md) - Plans navigation hub

> **Related Documents:**
> - [README.md](../README.md) - Project overview and features
> - [MISSION.md](../MISSION.md) - Mission statement and core principles

---

## 1. Project Integration Status

**Archived Plan:** [`plans/archive/PROJECT_INTEGRATION_PLAN.md`](plans/archive/PROJECT_INTEGRATION_PLAN.md)

### Current Merge Projects Status

The `merge_projects/` folder contains the following projects available for integration:

| Project | Status | Notes |
|---------|--------|-------|
| ai-factory | Available | AI factory patterns |
| balmasi-youtube-rag | Available | YouTube RAG implementation |
| compound-engineering-plugin | Available | Engineering plugin patterns |
| get-shit-done | Available | Task execution patterns |
| get-shit-done-2 | Available | Task execution patterns (v2) |
| LLM-Fine-tuning | Available | Fine-tuning workflows |
| Local-RAG-with-Ollama | Available | Local RAG with Ollama |
| Locally-Hosted-LM-Research-Assistant | Available | Research assistant patterns |
| mistral-vibe | Available | Skills system |
| MultiModal-RAG-with-Videos | Available | Multimodal RAG |
| OpenRAG | Available | Open RAG implementation |
| planning-with-files | Available | File-based planning |
| plano | Available | Orchestration patterns |
| RAG_Techniques | Available | RAG technique examples |
| RAG-Project | Available | RAG project reference |
| rag-youtube-assistant | Available | YouTube RAG assistant |
| Roo-Code | Available | Mode/tool patterns |
| superpowers | Available | Enhanced capabilities |
| svpino-youtube-rag | Available | YouTube RAG reference |
| unsloth | Available | Fine-tuning library |
| youtube-rag | Available | YouTube RAG patterns |

### Integration Approach

```bash
# Step 1: Analyze source project
cat merge_projects/<project-name>/README.md

# Step 2: Identify useful patterns/modules
# Step 3: Map to opencode_4py structure
# Step 4: Implement integration
# Step 5: Add tests
# Step 6: Document in docs/
```

---

## 2. Update Implementation Status

**Status File:** [`docs/IMPLEMENTATION_STATUS.md`](docs/IMPLEMENTATION_STATUS.md)

### Activation Steps

```bash
# Step 1: Run tests to get current coverage
cd src/opencode && python -m pytest --cov=src/opencode --cov-report=term-missing -q

# Step 2: Check implemented modules
ls -la src/opencode/src/opencode/

# Step 3: Update status file
# - Mark completed phases with ✅
# - Update coverage percentages
# - Add new completed components
```

### Update Template

```markdown
### [Date] Update

**Completed:**
- [ ] Module name - Coverage: XX%

**In Progress:**
- [ ] Module name - Status: description

**Coverage:** XX% (was YY%)
```

---

## 3. Execute the Testing Plan

**Plan File:** [`plans/TESTING_PLAN.md`](plans/TESTING_PLAN.md)

### Activation Steps

```bash
# Step 1: Run full test suite
cd src/opencode && python -m pytest src/opencode/tests/ --cov=src/opencode -v

# Step 2: Identify failing tests
cd src/opencode && python -m pytest src/opencode/tests/ --tb=short -x

# Step 3: Check coverage by module
cd src/opencode && python -m pytest --cov=src/opencode --cov-report=html
open src/opencode/htmlcov/index.html

# Step 4: Add tests for low-coverage modules
# Priority: providers (12-28%), CLI (18-35%), TUI (38-52%)
```

### Test Priority Matrix

| Priority | Module Area | Current Coverage | Target | Notes |
|----------|-------------|------------------|--------|-------|
| P0 | CLI Commands | 18-35% | 70% | High priority |
| P0 | TUI Widgets | 38-52% | 70% | User-facing |
| P1 | MCP Client | 32% | 70% | Protocol handling |
| P1 | Server Routes | 31-49% | 60% | API endpoints |
| -- | Providers | 12-28% | **Excluded** | External API wrappers |

**Note:** Provider implementations are excluded from coverage requirements as they are thin wrappers around external APIs. Focus on testing `provider/base.py` instead.

### Quick Commands

```bash
# Run specific test category
pytest src/opencode/tests/unit/ -v          # Unit tests
pytest src/opencode/tests/integration/ -v   # Integration tests
pytest src/opencode/tests/providers/ -v     # Provider tests

# Run with markers
pytest -m "not slow" -v                     # Skip slow tests
pytest -m "ollama" -v                       # Ollama tests only

# Generate coverage report
pytest --cov=src/opencode --cov-report=html --cov-report=term
```

---

## 4. Update Testing Status

**Status File:** [`docs/TESTING_STATUS.md`](docs/TESTING_STATUS.md)

### Activation Steps

```bash
# Step 1: Run tests and capture output
cd src/opencode && python -m pytest src/opencode/tests/ --cov=src/opencode --cov-report=term-missing -q > test_results.txt

# Step 2: Extract key metrics
# - Total tests
# - Pass/fail/skip counts
# - Coverage percentage
# - Low coverage modules

# Step 3: Update status file
# - Update summary table
# - Update coverage by module table
# - Add recent test additions
# - Update coverage goals progress
```

### Update Template

```markdown
## [Date] Test Run

**Results:**
- Total Tests: XXXX
- Passed: XXXX
- Failed: X
- Skipped: X
- Coverage: XX%

**Coverage Changes:**
| Module | Before | After | Change |
|--------|--------|-------|--------|
| provider/azure | 12% | 25% | +13% |

**New Tests Added:**
- test_provider_azure.py (XX tests)
- test_mcp_client_extended.py (XX tests)
```

---

## 5. ComfyUI Integration

**Status File:** [`plans/INTEGRATION_STATUS.md`](plans/INTEGRATION_STATUS.md)

The ComfyUI integration analysis is complete. See the status file for:
- System resources (CPU, GPU, network)
- Target project analysis
- Python environment details
- Integration points identified
- Recommended file locations

---

## Quick Reference

### File Locations

| Plan/Status | Location |
|-------------|----------|
| Project Index | `../PROJECT_INDEX.md` |
| Integration Plan (Archived) | `plans/archive/PROJECT_INTEGRATION_PLAN.md` |
| ComfyUI Integration Status | `plans/INTEGRATION_STATUS.md` |
| Implementation Status | `docs/IMPLEMENTATION_STATUS.md` |
| Testing Plan | `plans/TESTING_PLAN.md` |
| Testing Status | `docs/TESTING_STATUS.md` |
| Merge Projects | `merge_projects/` |
| Source Code | `src/opencode/src/opencode/` |
| Tests | `src/opencode/src/opencode/tests/` |

### Common Commands

```bash
# Full test suite with coverage
cd src/opencode && python -m pytest src/opencode/tests/ --cov=src/opencode --cov-report=term-missing -q

# Quick test run
cd src/opencode && python -m pytest src/opencode/tests/unit/ -v --tb=short

# Check specific module coverage
cd src/opencode && python -m pytest --cov=src/opencode.provider.azure --cov-report=term-missing

# List all tests
cd src/opencode && python -m pytest --collect-only -q
```

---

*Last Updated: 2026-02-24*
