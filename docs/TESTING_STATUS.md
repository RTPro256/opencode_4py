# Testing Status - OpenCode Python

This document tracks the current testing status, coverage metrics, and test results for the OpenCode Python project.

**Last Updated:** 2026-02-24

---

## Current Test Results

### Summary

| Metric | Value |
|--------|-------|
| **Total Tests** | 5700+ |
| **Passed** | 5697+ |
| **Failed** | 0 |
| **Skipped** | 3 |
| **Duration** | ~65 seconds |

### Code Coverage

| Metric | Value |
|--------|-------|
| **Total Statements** | 57,025 |
| **Covered Statements** | 52,598 |
| **Missed Statements** | 4,427 |
| **Coverage Percentage** | **90%** |

### Coverage Target

Per [TESTING_PLAN.md](../plans/TESTING_PLAN.md):
- **Minimum threshold:** 70% on non-excluded modules
- **Current status:** ✅ **90% - EXCEEDS TARGET**
- **Excluded modules:** Provider implementations (thin API wrappers)

---

## Coverage by Module

### High Coverage Modules (>80%)

| Module | Coverage | Status |
|--------|----------|--------|
| `core/config.py` | 95% | ✅ Excellent |
| `core/session.py` | 92% | ✅ Excellent |
| `core/context/tracker.py` | 95% | ✅ Excellent |
| `core/context/mentions.py` | 98% | ✅ Excellent |
| `core/context/checkpoints.py` | 81% | ✅ Good |
| `core/modes/base.py` | 90% | ✅ Excellent |
| `core/modes/registry.py` | 67% | ⚠️ Needs Work |
| `core/orchestration/agent.py` | 72% | ⚠️ Needs Work |
| `core/orchestration/coordinator.py` | 69% | ⚠️ Needs Work |
| `core/orchestration/router.py` | 80% | ✅ Good |
| `core/rag/retriever.py` | 98% | ✅ Excellent |
| `core/rag/evaluation.py` | 92% | ✅ Excellent |
| `core/rag/document.py` | 92% | ✅ Excellent |
| `core/rag/embeddings.py` | 82% | ✅ Good |
| `core/rag/query_rewriter.py` | 85% | ✅ Good |
| `core/rag/agent_rag_manager.py` | 98% | ✅ Excellent |
| `core/rag/safety/content_filter.py` | 97% | ✅ Excellent |
| `core/rag/safety/output_sanitizer.py` | 98% | ✅ Excellent |
| `core/rag/safety/audit_logger.py` | 82% | ✅ Good |
| `core/rag/validation/content_validator.py` | 99% | ✅ Excellent |
| `core/rag/validation/false_content_registry.py` | 71% | ⚠️ Needs Work |
| `core/subagents/manager.py` | 84% | ✅ Good |
| `core/subagents/types.py` | 100% | ✅ Excellent |
| `core/subagents/validator.py` | 99% | ✅ Excellent |
| `core/subagents/builtin.py` | 95% | ✅ Excellent |
| `core/video/frames.py` | 94% | ✅ Excellent |
| `core/youtube/chunking.py` | 95% | ✅ Excellent |
| `core/youtube/timestamps.py` | 97% | ✅ Excellent |
| `core/youtube/channel.py` | 94% | ✅ Excellent |
| `db/models.py` | 100% | ✅ Excellent |
| `router/engine.py` | 98% | ✅ Excellent |
| `router/config.py` | 100% | ✅ Excellent |
| `skills/discovery.py` | 95% | ✅ Excellent |
| `skills/manager.py` | 92% | ✅ Excellent |
| `skills/models.py` | 100% | ✅ Excellent |
| `llmchecker/ollama/client.py` | 85% | ✅ Good |
| `cli/commands/config.py` | 97% | ✅ Excellent |
| `cli/commands/llmchecker.py` | 84% | ✅ Good |
| `tool/explore.py` | 91% | ✅ Excellent |
| `tool/git.py` | 97% | ✅ Excellent |

### Medium Coverage Modules (50-79%)

| Module | Coverage | Status |
|--------|----------|--------|
| `core/context/checkpoints.py` | 81% | ✅ Good |
| `core/orchestration/router.py` | 80% | ✅ Good |
| `core/video/audio.py` | 81% | ✅ Good |
| `core/youtube/transcript.py` | 76% | ⚠️ Needs Work |
| `llmchecker/calibration/manager.py` | 65% | ⚠️ Needs Work |
| `llmchecker/hardware/detector.py` | 65% | ⚠️ Needs Work |
| `mcp/server.py` | 61% | ⚠️ Needs Work |
| `mcp/types.py` | 86% | ✅ Good |
| `i18n/manager.py` | 78% | ⚠️ Needs Work |
| `db/connection.py` | 70% | ⚠️ Needs Work |

### Low Coverage Modules (<50%)

| Module | Coverage | Status | Notes |
|--------|----------|--------|-------|
| `cli/commands/run.py` | 46% | ⚠️ Needs Work | CLI entry points |
| `cli/commands/serve.py` | 33% | ❌ Critical | Server startup |
| `cli/commands/auth.py` | 45% | ⚠️ Needs Work | Auth flows |
| `cli/main.py` | 65% | ⚠️ Needs Work | Main CLI |
| `tui/app.py` | 53% | ⚠️ Needs Work | TUI application |
| `tui/widgets/approval.py` | 35% | ❌ Critical | Approval widget |
| `tui/widgets/chat.py` | 50% | ⚠️ Needs Work | Chat widget |
| `tui/widgets/completion.py` | 30% | ❌ Critical | Completion widget |
| `tui/widgets/input.py` | 35% | ❌ Critical | Input widget |
| `tui/widgets/sidebar.py` | 55% | ⚠️ Needs Work | Sidebar widget |
| `mcp/client.py` | 69% | ⚠️ Needs Work | MCP client |
| `mcp/oauth.py` | 56% | ⚠️ Needs Work | OAuth flows |
| `server/app.py` | 96% | ✅ Excellent | Server app |
| `server/graphql/schema.py` | 43% | ⚠️ Needs Work | GraphQL schema |
| `server/routes/chat.py` | 42% | ⚠️ Needs Work | Chat routes |
| `server/routes/files.py` | 85% | ✅ Good | File routes |
| `server/routes/models.py` | 48% | ⚠️ Needs Work | Model routes |
| `server/routes/router.py` | 39% | ❌ Critical | Router routes |
| `server/routes/sessions.py` | 49% | ⚠️ Needs Work | Session routes |
| `server/routes/tools.py` | 39% | ❌ Critical | Tool routes |
| `server/routes/workflow.py` | 27% | ❌ Critical | Workflow routes |
| `core/rag/pipeline.py` | 40% | ❌ Critical | RAG pipeline |

### Excluded from Coverage (External API Wrappers)

The following modules are **thin wrappers around external APIs** and are excluded from coverage requirements. Testing these requires complex HTTP mocking with limited value:

| Module | Reason for Exclusion |
|--------|---------------------|
| `provider/anthropic.py` | External API wrapper |
| `provider/openai.py` | External API wrapper |
| `provider/ollama.py` | External API wrapper |
| `provider/groq.py` | External API wrapper |
| `provider/mistral.py` | External API wrapper |
| `provider/cohere.py` | External API wrapper |
| `provider/bedrock.py` | External API wrapper |
| `provider/azure.py` | External API wrapper |
| `provider/cerebras.py` | External API wrapper |
| `provider/deepinfra.py` | External API wrapper |
| `provider/google.py` | External API wrapper |
| `provider/lmstudio.py` | External API wrapper |
| `provider/openrouter.py` | External API wrapper |
| `provider/perplexity.py` | External API wrapper |
| `provider/together.py` | External API wrapper |
| `provider/vercel.py` | External API wrapper |
| `provider/xai.py` | External API wrapper |
| `provider/custom.py` | External API wrapper |

**Note:** Provider tests should focus on:
- Base provider class (`provider/base.py`) - already at 90% coverage
- Provider initialization and configuration
- Error handling patterns
- Response parsing logic

---

## Test Categories

### Unit Tests

| Category | Count | Status |
|----------|-------|--------|
| Core Tests | 245 | ✅ Passing |
| Context Tests | 89 | ✅ Passing |
| Orchestration Tests | 67 | ✅ Passing |
| RAG Tests | 124 | ✅ Passing |
| Provider Tests | 156 | ✅ Passing |
| YouTube Tests | 78 | ✅ Passing |
| Video Tests | 45 | ✅ Passing |
| LLMChecker Tests | 134 | ✅ Passing |
| Router Tests | 89 | ✅ Passing |
| Skills Tests | 56 | ✅ Passing |
| MCP Tests | 67 | ✅ Passing |
| DB Tests | 45 | ✅ Passing |
| I18n Tests | 78 | ✅ Passing |
| Tool Tests | 234 | ✅ Passing |
| Utility Tests | 156 | ✅ Passing |
| Server Tests | 89 | ✅ Passing |
| CLI Tests | 45 | ✅ Passing |
| TUI Tests | 67 | ✅ Passing |
| Session Tests | 52 | ✅ Passing |

### Integration Tests

| Test File | Tests | Status |
|-----------|-------|--------|
| `test_session_flow.py` | 12 | ✅ Passing |
| `test_workflow_execution.py` | 15 | ✅ Passing |
| `test_mcp_integration.py` | 18 | ✅ Passing |

### Provider Tests

| Provider | Tests | Status |
|----------|-------|--------|
| Base Provider | 25 | ✅ Passing |
| Anthropic | 29 | ✅ Passing |
| OpenAI | 33 | ✅ Passing |
| Ollama | 45 | ✅ Passing |
| Other Providers | 67 | ✅ Passing |

### Ollama Tests

| Test File | Tests | Status |
|-----------|-------|--------|
| `test_ollama_integration.py` | 15 | ✅ Passing |
| `test_ollama_accuracy.py` | 12 | ✅ Passing |
| `test_ollama_troubleshooting.py` | 10 | ✅ Passing |

### Prompt Tests

| Test File | Tests | Status |
|-----------|-------|--------|
| `test_prompt_comparison.py` | 8 | ✅ Passing |
| `test_prompt_accuracy.py` | 12 | ✅ Passing |

---

## Coverage Goals

### Target Coverage by Quarter

| Quarter | Target | Current | Status |
|---------|--------|---------|--------|
| Q1 2026 | 70% | 84% | ✅ Exceeded |
| Q2 2026 | 80% | 84% | ✅ Exceeded |
| Q3 2026 | 90% | - | 🔄 In Progress |
| Q4 2026 | 95% | - | 📋 Planned |

### Priority Areas for Coverage Improvement

1. **Server Routes** (Current: 27-85%)
   - `server/routes/workflow.py` at 27%
   - `server/routes/router.py` at 39%
   - `server/routes/tools.py` at 39%
   - Priority: High

2. **Tool Modules** (Current: 34%)
   - `tool/explore.py` at 34%
   - `tool/git.py` at 34%
   - Priority: High

3. **TUI Modules** (Current: 30-55%)
   - Need tests for widget interactions, event handling
   - Priority: Medium

4. **CLI Commands** (Current: 33-97%)
   - `cli/commands/serve.py` at 33%
   - `cli/commands/run.py` at 46%
   - Priority: Medium

---

## Test Infrastructure

### Test Framework
- **Framework:** pytest 9.0.2
- **Async Support:** pytest-asyncio 0.24.0
- **Coverage:** pytest-cov 7.0.0
- **Python Version:** 3.14.3

### Test Commands

```bash
# Run all tests with coverage
pytest src/opencode/tests/ --cov=src/opencode --cov-report=term-missing

# Run specific test category
pytest src/opencode/tests/unit/ -v
pytest src/opencode/tests/integration/ -v
pytest src/opencode/tests/providers/ -v

# Run with specific markers
pytest -m "not slow" -v
pytest -m "ollama" -v

# Generate HTML coverage report
pytest --cov=src/opencode --cov-report=html
```

### CI/CD Integration

Tests run automatically on:
- Every push to `main` and `develop` branches
- Every pull request to `main`
- Scheduled runs for prompt accuracy benchmarks (weekly)

---

## Recent Test Additions

### 2026-02-24
- Added models routes tests (22 tests) - models.py now at 100%
- Added sessions routes tests (23 tests) - sessions.py now at 100%
- Added extended chart node tests (56 tests) - chart.py improved from 42% to 53%
- Added TUI logging tests (12 tests)
- Added sandbox tests (27 tests) - sandbox.py improved from 27% to 83%
- Added RAG share tests (22 tests) - rag_share.py improved from 9% to 63%
- Added RAG validation tests (7 tests) - rag_validation.py improved from 13% to 35%
- Added custom provider tests (14 tests) - custom.py improved from 14% to 39%
- Added Google provider tests (21 tests) - google.py improved from 15% to 49%

### 2026-02-22
- Added RAG evaluation tests (15 tests)
- Added query rewriter tests (12 tests)
- Added video audio/frames tests (18 tests)
- Added YouTube transcript/timestamps/chunking tests (25 tests)
- Added todo tool tests (12 tests)
- Added extended Anthropic provider tests (29 tests)
- Added extended OpenAI provider tests (33 tests)
- Added LLMChecker CLI tests (15 tests)
- Added LLMChecker CLI extended tests (27 tests)
- Added TUI widgets extended tests (43 tests)
- Added MCP client extended tests (36 tests)
- **Added YouTube channel tests (26 tests)** - Tests for `ChannelStats`, `VideoInfo`, `YouTubeChannelIndexer`
- **Added workflow routes tests (36 tests)** - Tests for workflow CRUD, execution, GPU management
- **Added explore tool tests (49 tests)** - Tests for index loading, section extraction, query answering
- **Added git tool tests (47 tests)** - Tests for all git operations

### Coverage Progress
- Started at: 49%
- Previous: 84%
- Current: 88%
- Total Improvement: +39 percentage points

---

## Known Issues

### Skipped Tests (3)
1. `test_multiedit_tool.py::test_permission_denied` - File permission test not applicable on Windows
2. `test_multiedit_tool.py::test_readonly_file` - File permission test not applicable on Windows
3. `test_subagent_manager.py::test_code_agent` - No builtin 'code' agent

### Flaky Tests
None currently identified.

---

## Test Maintenance

### Adding New Tests
1. Create test file in appropriate directory under `src/opencode/tests/`
2. Follow naming convention: `test_<module_name>.py`
3. Use fixtures from `conftest.py`
4. Add appropriate markers (`@pytest.mark.asyncio`, `@pytest.mark.slow`, etc.)

### Running Tests Before Commit
```bash
# Quick test run
pytest src/opencode/tests/unit/ -v --tb=short

# Full test suite with coverage
pytest src/opencode/tests/ --cov=src/opencode --cov-report=term-missing
```

---

*This document is automatically updated as part of the CI/CD pipeline.*
