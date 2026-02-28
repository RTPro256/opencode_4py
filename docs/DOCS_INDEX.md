# OpenCode Python - Documentation Index

> **Navigation Hub** - Quick access to all OpenCode documentation

---

## Quick Links

| Resource | Description |
|----------|-------------|
| [README.md](../README.md) | Project overview and quick start |
| [TODO.md](../TODO.md) | Task tracking and pending work |
| [CHANGELOG.md](../CHANGELOG.md) | Version history and changes |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Contribution guidelines |
| [SECURITY.md](../SECURITY.md) | Security policy |
| [PLAN_INDEX.md](../plans/PLAN_INDEX.md) | All plans and project tracking |
| [QUICK_START_COMMANDS.md](../plans/QUICK_START_COMMANDS.md) | Merge/integrate/sync workflows |

---

## Documentation Categories

### Getting Started

| Document | Description | Status |
|----------|-------------|--------|
| [README.md](README.md) | Full documentation with installation, configuration, and usage | Active |
| [sessions/README.md](sessions/README.md) | Session management documentation | Active |

### Architecture & Design

| Document | Description | Status |
|----------|-------------|--------|
| [AGENT_MODEL_ORCHESTRATION.md](AGENT_MODEL_ORCHESTRATION.md) | Agent and model orchestration architecture | Active |
| [WORKFLOW_ENGINE.md](WORKFLOW_ENGINE.md) | Workflow engine design and implementation | Active |
| [FILE_SYSTEM_SANDBOXING.md](FILE_SYSTEM_SANDBOXING.md) | File system security and sandboxing | Active |

### Implementation Status

| Document | Description | Status |
|----------|-------------|--------|
| [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) | Current implementation status | Active |
| [FEATURE_COVERAGE.md](FEATURE_COVERAGE.md) | Feature coverage matrix | Active |
| [FEATURE_VERIFICATION.md](FEATURE_VERIFICATION.md) | Feature verification & architecture maps | NEW |
| [TESTING_STATUS.md](TESTING_STATUS.md) | Test coverage and status | Active |
| [CODE_ANALYSIS_REPORT.md](CODE_ANALYSIS_REPORT.md) | Code quality analysis | Active |

### Review Reports

| Document | Description | Status |
|----------|-------------|--------|
| [TUI_FEATURE_REVIEW.md](TUI_FEATURE_REVIEW.md) | TUI feature completeness review | Active |
| [CONFIGURATION_REVIEW.md](CONFIGURATION_REVIEW.md) | Configuration complexity review | Active |
| [ONBOARDING_REVIEW.md](ONBOARDING_REVIEW.md) | Onboarding experience review | Active |
| [RAG_ARCHITECTURE_REVIEW.md](RAG_ARCHITECTURE_REVIEW.md) | RAG architecture review | Active |
| [RAG_TEST_COVERAGE_REVIEW.md](RAG_TEST_COVERAGE_REVIEW.md) | RAG test coverage review | Active |

> **Archived:** [RAG_ERROR_PREVENTION_AUDIT.md](archive/RAG_ERROR_PREVENTION_AUDIT.md) - Moved to [`RAG/troubleshooting/AUDIT_SUMMARY.md`](../RAG/troubleshooting/AUDIT_SUMMARY.md)

### Style & Guidelines

| Document | Description | Status |
|----------|-------------|--------|
| [STYLE_GUIDE.md](STYLE_GUIDE.md) | Documentation style guide | Active |
| [PLAN_EXTRACTION_REVIEW.md](PLAN_EXTRACTION_REVIEW.md) | Review of plans for doc extraction opportunities | Active |
| [BUG_DETECTION_PROCESS.md](BUG_DETECTION_PROCESS.md) | Bug detection and RAG documentation process | Active |

### Testing

| Document | Description | Status | Related Plan |
|----------|-------------|--------|--------------|
| [TESTING_INFRASTRUCTURE.md](TESTING_INFRASTRUCTURE.md) | Test directory structure and configuration | Active | [TESTING_PLAN.md](../plans/TESTING_PLAN.md) |
| [PROMPT_TESTING.md](PROMPT_TESTING.md) | Cross-model prompt comparison and accuracy benchmarks | Active | [TESTING_PLAN.md](../plans/TESTING_PLAN.md) |
| [OLLAMA_TESTING.md](OLLAMA_TESTING.md) | Ollama integration, accuracy, and troubleshooting tests | Active | [TESTING_PLAN.md](../plans/TESTING_PLAN.md) |
| [CI_CD_TESTING.md](CI_CD_TESTING.md) | pytest configuration and GitHub Actions workflows | Active | [TESTING_PLAN.md](../plans/TESTING_PLAN.md) |
| [TEST_MAINTENANCE_GUIDE.md](TEST_MAINTENANCE_GUIDE.md) | Guidelines for adding and maintaining tests | Active | [TESTING_PLAN.md](../plans/TESTING_PLAN.md) |
| [TEST_DISCOVERY.md](TEST_DISCOVERY.md) | Test discovery commands for new code and features | Active | [TESTING_PLAN.md](../plans/TESTING_PLAN.md) |
| [TESTING_STATUS.md](TESTING_STATUS.md) | Test coverage and status | Active | [TESTING_PLAN.md](../plans/TESTING_PLAN.md) |

> See [TESTING_PLAN.md](../plans/TESTING_PLAN.md) for the comprehensive testing strategy overview.

### API Reference

| Document | Description | Status |
|----------|-------------|--------|
| [api/rag-methods-api.md](api/rag-methods-api.md) | RAG methods API reference | Active |
| [api/finetuning-api.md](api/finetuning-api.md) | Fine-tuning API reference | Active |

### Integration & Migration

| Document | Description | Status |
|----------|-------------|--------|
| [INTEGRATION_PLAN.md](INTEGRATION_PLAN.md) | Integration planning | Active |
| [TARGET_PROJECT_FOR_TESTING_COMPARE.md](TARGET_PROJECT_FOR_TESTING_COMPARE.md) | Plan duplication analysis | Active |
| [GITHUB_REPOSITORIES.md](GITHUB_REPOSITORIES.md) | Repository reference and configuration | Reference |
| [MIGRATION_PLAN.md](../plans/archive/MIGRATION_PLAN.md) | Migration from TypeScript (archived) | Archived |
| [INTEGRATION_POSTMORTEM.md](../plans/archive/INTEGRATION_POSTMORTEM.md) | Integration lessons learned | Archived |

### Merged Projects

| Source Project | Category | Integrated Features | Status |
|----------------|----------|--------------------| -------|
| Local-RAG-with-Ollama | RAG Core | Local embedding support | Integrated |
| OpenRAG | RAG Core | 9 RAG methods (NaiveRAG, SelfRAG, etc.) | Integrated |
| RAG-Project | RAG Core | Core RAG components | Pending |
| RAG_Techniques | RAG Core | HyDe, Fusion, advanced patterns | Integrated |
| balmasi-youtube-rag | YouTube RAG | Video transcription | Pending |
| rag-youtube-assistant | YouTube RAG | Video search, timestamps | Pending |
| svpino-youtube-rag | YouTube RAG | Video processing | Pending |
| youtube-rag | YouTube RAG | Content extraction | Pending |
| MultiModal-RAG-with-Videos | YouTube RAG | Multimodal embeddings | Pending |
| LLM-Fine-tuning | Fine-tuning | Dataset preparation, formatters | Integrated |
| unsloth | Fine-tuning | LoRA/QLoRA configuration | Integrated |
| Roo-Code | Code Assistant | Code generation patterns | Pending |
| get-shit-done | Code Assistant | Task automation | Pending |
| get-shit-done-2 | Code Assistant | Enhanced automation | Pending |
| superpowers | Code Assistant | Power user tools | Pending |
| planning-with-files | Planning | File-based planning | Pending |
| plano | Planning | Task decomposition | Pending |
| ai-factory | Infrastructure | Model factory patterns | Pending |
| compound-engineering-plugin | Infrastructure | Plugin architecture | Pending |
| mistral-vibe | Infrastructure | Mistral provider support | Pending |
| Locally-Hosted-LM-Research-Assistant | Infrastructure | Research workflows | Pending |

> See [MERGE_INTEGRATION_PLAN.md](../plans/MERGE_INTEGRATION_PLAN.md) for detailed integration planning.

**Naming Convention**: Completed projects are renamed with `--delete` suffix (e.g., `Local-RAG-with-Ollama--delete`) to indicate safe deletion.

### RAG (Retrieval-Augmented Generation)

| Document | Description | Status |
|----------|-------------|--------|
| [BEST_PRACTICE_FOR_RAG.MD](BEST_PRACTICE_FOR_RAG.MD) | RAG best practices guide | Active |
| [RAG_SHARING.md](RAG_SHARING.md) | RAG sharing between agents | Active |

---

## RAG Troubleshooting

### Error Documentation

Located in [`RAG/troubleshooting/errors/`](../RAG/troubleshooting/errors/):

| Error ID | Description |
|----------|-------------|
| [ERR-001](../RAG/troubleshooting/errors/ERR-001-cli-command-structure.md) | CLI command structure issues |
| [ERR-002](../RAG/troubleshooting/errors/ERR-002-sqlalchemy-syntax.md) | SQLAlchemy 2.x syntax |
| [ERR-003](../RAG/troubleshooting/errors/ERR-003-ai-provider-availability.md) | AI provider availability |
| [ERR-004](../RAG/troubleshooting/errors/ERR-004-missing-preflight-checks.md) | Missing preflight checks |
| [ERR-005](../RAG/troubleshooting/errors/ERR-005-web-framework-response-types.md) | Web framework response types |
| [ERR-006](../RAG/troubleshooting/errors/ERR-006-dependency-version-warnings.md) | Dependency version warnings |
| [ERR-007](../RAG/troubleshooting/errors/ERR-007-wrong-provider-class.md) | Wrong provider class |
| [ERR-008](../RAG/troubleshooting/errors/ERR-008-single-line-input-widget.md) | Single-line input widget |
| [ERR-009](../RAG/troubleshooting/errors/ERR-009-wrong-provider-method-name.md) | Wrong provider method name |
| [ERR-010](../RAG/troubleshooting/errors/ERR-010-async-generator-await.md) | Async generator await |
| [ERR-011](../RAG/troubleshooting/errors/ERR-011-runtime-logging-silent-failures.md) | Runtime logging silent failures |
| [ERR-012](../RAG/troubleshooting/errors/ERR-012-missing-parameter-init.md) | Missing parameter init |
| [ERR-013](../RAG/troubleshooting/errors/ERR-013-session-log-storage-location.md) | Session log storage location |
| [ERR-014](../RAG/troubleshooting/errors/ERR-014-reactive-property-watch-missing.md) | Reactive property watch missing |
| [ERR-015](../RAG/troubleshooting/errors/ERR-015-installed-vs-source-mismatch.md) | Installed vs source mismatch |
| [ERR-016](../RAG/troubleshooting/errors/ERR-016-mutation-observer-button.md) | Mutation observer button |
| [ERR-017](../RAG/troubleshooting/errors/ERR-017-comfyui-button-selector.md) | ComfyUI button selector |

### Patterns & Workflows

| Type | Document |
|------|----------|
| Pattern | [PATTERN-001-tui-stall-diagnosis.md](../RAG/troubleshooting/patterns/PATTERN-001-tui-stall-diagnosis.md) |
| Pattern | [PATTERN-002-provider-connection.md](../RAG/troubleshooting/patterns/PATTERN-002-provider-connection.md) |
| Pattern | [PATTERN-003-integration-verification.md](../RAG/troubleshooting/patterns/PATTERN-003-integration-verification.md) |
| Workflow | [WORKFLOW-001-tui-troubleshooting.md](../RAG/troubleshooting/workflows/WORKFLOW-001-tui-troubleshooting.md) |
| Workflow | [WORKFLOW-002-integration-troubleshooting.md](../RAG/troubleshooting/workflows/WORKFLOW-002-integration-troubleshooting.md) |

---

## Examples

Located in [`examples/`](../examples/):

| Example | Description |
|---------|-------------|
| [basic_usage.py](../examples/basic_usage.py) | Basic OpenCode usage |
| [provider_config.py](../examples/provider_config.py) | Provider configuration examples |
| [rag_example.py](../examples/rag_example.py) | RAG usage example |

---

## Configuration Presets

Located in [`config/presets/`](../config/presets/):

| Preset | Description |
|--------|-------------|
| [claude.toml](../config/presets/claude.toml) | Anthropic Claude configuration |
| [openai.toml](../config/presets/openai.toml) | OpenAI GPT configuration |
| [local.toml](../config/presets/local.toml) | Local Ollama configuration |
| [multi-provider.toml](../config/presets/multi-provider.toml) | Multi-provider setup |

---

## Document Status Legend

| Status | Description |
|--------|-------------|
| Active | Currently maintained and accurate |
| In Progress | Being actively developed |
| Complete | Finished, may be archived |
| Archive Candidate | Completed, recommended for archival |
| Reference | Historical reference value |

---

*Last updated: 2026-02-25*
