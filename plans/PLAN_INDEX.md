h# OpenCode Python - Plans Index

> **Navigation Hub** - Quick access to all OpenCode planning documents

---

## Quick Links

| Resource | Description |
|----------|-------------|
| [README.md](../README.md) | Project overview and quick start |
| [TODO.md](../TODO.md) | Task tracking and pending work |
| [CHANGELOG.md](../CHANGELOG.md) | Version history and changes |
| [DOCS_INDEX.md](../docs/DOCS_INDEX.md) | Documentation navigation |

---

## Active Plans

### Development Plans

| Plan | Description | Status | Related Docs |
|------|-------------|--------|--------------|
| [FEATURE_GENERATION_PLAN.md](FEATURE_GENERATION_PLAN.md) | Simple prompts for feature/code generation | Active | - |
| [CODE_IMPROVEMENT_PLAN.md](CODE_IMPROVEMENT_PLAN.md) | Code quality, type safety, and best practices | Active | - |
| [TESTING_PLAN.md](TESTING_PLAN.md) | Testing strategy and coverage goals | Active | [6 docs](../docs/DOCS_INDEX.md#testing) |
| [USER_ACCEPTANCE_TESTING.md](USER_ACCEPTANCE_TESTING.md) | UAT validation for integrated features | Active | - |
| [DOCUMENTATION_PLAN.md](DOCUMENTATION_PLAN.md) | Documentation strategy and standards | Active | - |
| [PRIVACY_FIRST_RAG_PLAN.md](PRIVACY_FIRST_RAG_PLAN.md) | Privacy-focused RAG implementation | Active | - |

### Project Organization

| Plan | Description | Status |
|------|-------------|--------|
| [PROJECT_ORGANIZATION_PLAN.md](PROJECT_ORGANIZATION_PLAN.md) | Project structure and naming conventions | Complete |
| [PROJECT_REVIEW_FINDINGS.md](PROJECT_REVIEW_FINDINGS.md) | Review findings and recommendations | Active |
| [COMPREHENSIVE_PROJECT_REVIEW_PLAN.md](COMPREHENSIVE_PROJECT_REVIEW_PLAN.md) | Comprehensive review plan | Complete |

### Infrastructure

| Plan | Description | Status |
|------|-------------|--------|
| [MERGE_INTEGRATION_PLAN.md](MERGE_INTEGRATION_PLAN.md) | Integrate external projects from merge_projects/ | Active |
| [GITHUB_UPLOAD_PLAN.md](GITHUB_UPLOAD_PLAN.md) | GitHub upload with Git LFS | In Progress |
| [GITHUB_REPOSITORIES.md](../docs/GITHUB_REPOSITORIES.md) | Repository reference and configuration | Reference |
| [TARGET_PROJECT_SYNC_PLAN.md](TARGET_PROJECT_SYNC_PLAN.md) | Sync changes to target projects | Active |
| [FOR_TESTING_PLAN.md](FOR_TESTING_PLAN.md) | Testing infrastructure setup | Active |
| [INTEGRATION_STATUS.md](INTEGRATION_STATUS.md) | ComfyUI integration status | Active |

### User Experience

| Plan | Description | Status |
|------|-------------|--------|
| [SIMPLIFIED_TROUBLESHOOTING_UX_PLAN.md](SIMPLIFIED_TROUBLESHOOTING_UX_PLAN.md) | Simplified troubleshooting UX | Active |
| [FOR_TESTING_UPDATE_PLAN.md](FOR_TESTING_UPDATE_PLAN.md) | TUI stall troubleshooting | Active |

### Execution Guides

| Plan | Description | Status |
|------|-------------|--------|
| [QUICK_START_COMMANDS.md](QUICK_START_COMMANDS.md) | Simple prompts for merge/integrate/sync | Active |
| [PLAN_EXECUTION_GUIDE.md](PLAN_EXECUTION_GUIDE.md) | Guide for executing plans | Active |

---

## Archived Plans

Located in [`archive/`](archive/):

| Plan | Description | Status |
|------|-------------|--------|
| [archive/MIGRATION_PLAN.md](archive/MIGRATION_PLAN.md) | TypeScript to Python migration | Archived |
| [archive/PROJECT_INTEGRATION_PLAN.md](archive/PROJECT_INTEGRATION_PLAN.md) | Project integration planning | Archived |
| [archive/MULTI_MODEL_IMPLEMENTATION_PLAN.md](archive/MULTI_MODEL_IMPLEMENTATION_PLAN.md) | Multi-model infrastructure | Archived |
| [archive/INTEGRATION_POSTMORTEM.md](archive/INTEGRATION_POSTMORTEM.md) | Integration lessons learned | Archived |

> See [`archive/README.md`](archive/README.md) for archive details.

---

## Plan Categories

### By Status

| Status | Count | Plans |
|--------|-------|-------|
| Active | 14 | FEATURE_GENERATION_PLAN, CODE_IMPROVEMENT_PLAN, TESTING_PLAN, USER_ACCEPTANCE_TESTING, DOCUMENTATION_PLAN, PRIVACY_FIRST_RAG_PLAN, PROJECT_REVIEW_FINDINGS, TARGET_PROJECT_SYNC_PLAN, FOR_TESTING_PLAN, INTEGRATION_STATUS, SIMPLIFIED_TROUBLESHOOTING_UX_PLAN, FOR_TESTING_UPDATE_PLAN, MERGE_INTEGRATION_PLAN, QUICK_START_COMMANDS |
| Complete | 2 | PROJECT_ORGANIZATION_PLAN, COMPREHENSIVE_PROJECT_REVIEW_PLAN |
| In Progress | 1 | GITHUB_UPLOAD_PLAN |
| Archived | 4 | MIGRATION_PLAN, PROJECT_INTEGRATION_PLAN, MULTI_MODEL_IMPLEMENTATION_PLAN, INTEGRATION_POSTMORTEM |

### By Priority

| Priority | Plans |
|----------|-------|
| High | CODE_IMPROVEMENT_PLAN, TESTING_PLAN, GITHUB_UPLOAD_PLAN, MERGE_INTEGRATION_PLAN |
| Medium | DOCUMENTATION_PLAN, PRIVACY_FIRST_RAG_PLAN, PROJECT_REVIEW_FINDINGS |
| Low | PROJECT_ORGANIZATION_PLAN, FOR_TESTING_PLAN |

---

## Related Documentation

### Documentation Index

See [DOCS_INDEX.md](../docs/DOCS_INDEX.md) for:
- Architecture documentation
- Implementation status
- Feature coverage
- Testing status
- RAG documentation

### RAG Resources

- [RAG/README.md](../RAG/README.md) - RAG system overview
- [RAG/troubleshooting/](../RAG/troubleshooting/) - Error documentation and patterns

---

## Plan Lineage

Track plan relationships and dependencies:

| Plan | Derived From | Related Plans |
|------|--------------|---------------|
| [MERGE_INTEGRATION_PLAN.md](MERGE_INTEGRATION_PLAN.md) | PLAN_INDEX.md, DOCS_INDEX.md review | PRIVACY_FIRST_RAG_PLAN, CODE_IMPROVEMENT_PLAN |
| [FOR_TESTING_UPDATE_PLAN.md](FOR_TESTING_UPDATE_PLAN.md) | FOR_TESTING_PLAN | SIMPLIFIED_TROUBLESHOOTING_UX_PLAN |
| [PROJECT_REVIEW_FINDINGS.md](PROJECT_REVIEW_FINDINGS.md) | COMPREHENSIVE_PROJECT_REVIEW_PLAN | CODE_IMPROVEMENT_PLAN, TESTING_PLAN |
| [INTEGRATION_STATUS.md](INTEGRATION_STATUS.md) | archive/PROJECT_INTEGRATION_PLAN | TARGET_PROJECT_SYNC_PLAN |

> Plans can be derived from reviews of other plans or documents. This section tracks those relationships.

---

## Plan Status Legend

| Status | Description |
|--------|-------------|
| Active | Currently being worked on or referenced |
| In Progress | Implementation in progress |
| Complete | Finished, may be archived |
| Archived | Historical reference only |

---

## Quick Reference

### Most Referenced Plans

1. **[FEATURE_GENERATION_PLAN.md](FEATURE_GENERATION_PLAN.md)** - Feature generation workflow
2. **[TESTING_PLAN.md](TESTING_PLAN.md)** - Testing strategy and coverage
3. **[CODE_IMPROVEMENT_PLAN.md](CODE_IMPROVEMENT_PLAN.md)** - Code quality standards

### New Start Here

1. Read [README.md](../README.md) for project overview
2. Check [TODO.md](../TODO.md) for current tasks
3. **Use [QUICK_START_COMMANDS.md](QUICK_START_COMMANDS.md) for merge/integrate/sync workflows**
4. Review [FEATURE_GENERATION_PLAN.md](FEATURE_GENERATION_PLAN.md) for feature generation
5. See [CODE_IMPROVEMENT_PLAN.md](CODE_IMPROVEMENT_PLAN.md) for coding standards

---

*Last updated: 2026-02-25*
