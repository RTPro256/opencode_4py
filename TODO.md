# OpenCode Python - TODO List

This file tracks all pending and completed tasks for the OpenCode Python project, organized by source document.

## Status Legend
- [x] Completed
- [ ] Pending
- [-] In Progress

---

# Plans Directory TODOs

## plans/CODE_IMPROVEMENT_PLAN.md

### Part 1: Python Code Standards

#### 1.1 Type Safety and Static Analysis
- [ ] Add `mypy --strict` to CI pipeline
- [ ] Add type hints to all public functions
- [ ] Create Protocol definitions for major interfaces
- [ ] Use TypeGuard for runtime validation of external data

#### 1.2 Error Handling Standards
- [ ] Create unified exception hierarchy
- [ ] Implement Result pattern for recoverable errors
- [ ] Add context managers for all resources
- [ ] Document error handling patterns

#### 1.3 Async Best Practices
- [ ] Convert remaining sync code to async
- [ ] Add proper cancellation handling
- [ ] Implement rate limiting for all external calls
- [ ] Add timeout handling for all I/O operations

### Part 2: Security Improvements

#### 2.1 Input Validation
- [ ] Add Pydantic validation to all API endpoints
- [ ] Implement path validation for all file operations
- [ ] Add input sanitization for shell commands
- [ ] Create validation middleware for FastAPI

#### 2.2 Secrets Management
- [ ] Implement SecretsManager abstraction
- [ ] Add secret filtering to all loggers
- [ ] Document secrets management best practices
- [ ] Add audit logging for secret access

#### 2.3 Dependency Security
- [ ] Pin all dependency versions
- [ ] Add dependency scanning to CI
- [ ] Set up automated dependency updates (Dependabot)
- [ ] Create security policy document

### Part 3: Framework Improvements

#### 3.1 FastAPI Best Practices
- [ ] Add request validation middleware
- [ ] Implement dependency injection pattern
- [ ] Add rate limiting to all endpoints
- [ ] Add request tracing

#### 3.2 SQLAlchemy Best Practices
- [ ] Use async session properly
- [ ] Use repository pattern
- [ ] Add connection pooling
- [ ] Implement proper transaction handling

---

## plans/DOCUMENTATION_PLAN.md

### Phase 1: Foundation
- [x] Create documentation directory structure
- [x] Establish style guide
- [ ] Set up CI for docs
- [x] Migrate existing docs to new structure

### Phase 2: Core Documentation
- [ ] Complete API reference
- [ ] Write architecture documentation
- [ ] Create troubleshooting guide
- [ ] Add provider-specific guides

### Phase 3: Tutorials & Guides
- [ ] Create tutorial series
- [ ] Add video walkthroughs (optional)
- [ ] Create interactive examples
- [ ] Write contributor guides

### Phase 4: Polish & Maintenance
- [ ] Set up automated API docs
- [ ] Create documentation website
- [ ] Implement search functionality
- [ ] Establish review schedule

### Documentation Gaps
- [ ] No API reference documentation
- [ ] No architecture diagrams
- [ ] No tutorial series
- [ ] No troubleshooting guide
- [ ] No contributor guidelines (beyond CONTRIBUTING.md)
- [ ] No video/walkthrough content

---

## plans/TESTING_PLAN.md

### Unit Tests
- [ ] Workflow engine tests
- [ ] Node execution tests
- [ ] Router decision tests
- [ ] VRAM monitoring tests (mocked)
- [ ] Cache tests

### Integration Tests
- [ ] End-to-end workflow execution
- [ ] Router with real backends
- [ ] GraphQL API tests
- [ ] WebSocket subscription tests

### Performance Tests
- [ ] Workflow execution latency
- [ ] Router decision latency
- [ ] Cache hit rate benchmarks
- [ ] Memory usage profiling

---

# Docs Directory TODOs

## docs/FEATURE_COVERAGE.md

### Agents
- [ ] Implement `general` subagent for complex searches and multi-step operations

### Desktop Application
- [ ] macOS (Apple Silicon) - Not planned (Tauri-based)
- [ ] macOS (Intel) - Not planned (Tauri-based)
- [ ] Windows - Not planned (Tauri-based)
- [ ] Linux - Not planned (Tauri-based)

> Note: Python version focuses on CLI/TUI and HTTP server. Desktop app not planned.

---

## docs/IMPLEMENTATION_STATUS.md

### Next Steps (Optional Enhancements)
- [ ] Add more comprehensive unit tests
- [ ] Implement Google API tools (requires OAuth credentials)
- [ ] Add integration tests
- [ ] Performance optimization
- [ ] Documentation improvements

### Optional Components (Not Implemented)
- [ ] `workflow/tools/google/calendar.py` - Google Calendar API
- [ ] `workflow/tools/google/drive.py` - Google Drive API
- [ ] `workflow/tools/google/gmail.py` - Gmail API

---

# Test Suite Tasks

## Completed
- [x] Analyze project test configuration and structure
- [x] Set up test environment (install dependencies)
- [x] Run complete test suite with coverage
- [x] Fix failing tests (3 failures)
- [x] Improve test coverage (from 12% to 29%)
- [x] Fix source code bugs in explore.py and memory.py
- [x] Continue testing - added 20+ new test files
- [x] Add tests for CLI command execution paths
- [x] Add tests for provider implementations
- [x] Add tests for workflow nodes and tools
- [x] Add tests for RAG components
- [x] Add tests for LLMChecker components
- [x] Final verification - all tests passing (647 tests, 29% coverage)
- [x] Review and add missing projects from merge_projects to MIGRATION_PLAN.md

## Pending - Test Coverage Improvements
- [ ] Add integration tests for provider API interactions
- [ ] Add tests for CLI command execution paths with mocked dependencies
- [ ] Add edge case and error handling tests for tool implementations
- [x] Register `@pytest.mark.unit` in `pyproject.toml` to eliminate warnings
- [x] Add tests for hardware detection backends (CUDA, ROCm, Apple, Intel)
- [ ] Add tests for workflow engine execution paths

---

# Immediate Action Items (2026-02-24)

## Completed
- [x] Create `docs/INDEX.md` navigation document
- [x] Create `plans/archive/` directory
- [x] Move completed plans to archive:
  - `MIGRATION_PLAN.md`
  - `PROJECT_INTEGRATION_PLAN.md`
  - `MULTI_MODEL_IMPLEMENTATION_PLAN.md`
  - `INTEGRATION_POSTMORTEM.md`
- [x] Update `TODO.md` to remove completed items
- [x] Add configuration presets for common setups
- [x] Split `rag.py` into focused modules:
  - `rag_create.py` - RAG index creation commands
  - `rag_query.py` - RAG query commands
  - `rag_manage.py` - RAG management commands (add, status, clear, stats)
  - `rag_validation.py` - Content validation commands
  - `rag_share.py` - Community RAG sharing commands
  - `rag_audit.py` - Audit log commands
- [x] Create `opencode config wizard` command

## Pending
- [ ] Create interactive tutorial
- [x] Improve test coverage to 50%+ (currently at 71%)

---

# Notes

## Test Coverage Summary (Current: 71%)
- **100% coverage**: `__init__.py` files, `config.py` (router), `models.py` (db), `types.py` (subagents)
- **High coverage (70%+)**: `tracker.py` (95%), `mcp/types.py` (85%), `memory.py` (84%), `hardware/models.py` (82%)
- **Moderate coverage (40-70%)**: Provider base, orchestration, session, workflow models

## Files Modified During Test Suite Work
- `src/opencode/src/opencode/tool/explore.py` - Fixed import and Tool interface
- `src/opencode/src/opencode/tool/memory.py` - Fixed import and Tool interface
- `src/opencode/src/opencode/core/config.py` - Fixed Python 3.14 compatibility (tomllib)
- `src/opencode/src/opencode/tests/providers/test_ollama_provider.py` - Fixed method name and mock pattern
- `src/opencode/src/opencode/tests/unit/test_context.py` - Fixed assertion

## New Test Files Created (20+)
- `test_cli_commands.py`, `test_cli_commands_extended.py`, `test_cli_main.py`
- `test_provider_implementations.py`, `test_providers.py`
- `test_workflow.py`, `test_workflow_nodes.py`
- `test_rag.py`
- `test_llmchecker.py`, `test_llmchecker_commands.py`
- `test_explore_tool.py`, `test_memory_tool.py`, `test_tools.py`
- `test_db.py`, `test_tui.py`, `test_i18n.py`, `test_skills.py`
- `test_video.py`, `test_youtube.py`, `test_server.py`, `test_router.py`
- `test_mcp_oauth.py`, `test_util.py`

---

*Last updated: 2026-02-24*
