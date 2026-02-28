# Quick Start Commands

> **Simple prompts to start common integration workflows**

---

## Overview

This document provides ready-to-use prompts for starting common integration workflows. Copy and paste these commands to quickly begin working on merge, integration, or sync operations.

---

## Command Reference

### 1. Merge Project to OpenCode

**Purpose**: Merge a project from `merge_projects/` into opencode_4py

**Prompt**:
```
Start merge of [PROJECT_NAME] from merge_projects/ into opencode_4py.

Reference: plans/MERGE_INTEGRATION_PLAN.md

Steps:
1. Analyze merge_projects/[PROJECT_NAME]/ structure and dependencies
2. Map features to opencode_4py architecture
3. Integrate code following CODE_IMPROVEMENT_PLAN.md standards
4. Add tests per TESTING_PLAN.md
5. Update documentation
6. Rename folder to [PROJECT_NAME]--delete when complete
```

**Example**:
```
Start merge of Local-RAG-with-Ollama from merge_projects/ into opencode_4py.

Reference: plans/MERGE_INTEGRATION_PLAN.md

Steps:
1. Analyze merge_projects/Local-RAG-with-Ollama/ structure and dependencies
2. Map features to opencode_4py architecture
3. Integrate code following CODE_IMPROVEMENT_PLAN.md standards
4. Add tests per TESTING_PLAN.md
5. Update documentation
6. Rename folder to Local-RAG-with-Ollama--delete when complete
```

---

### 2. Integrate OpenCode to Project

**Purpose**: Integrate opencode_4py capabilities into a target project in `for_testing/`

**Prompt**:
```
Start integration of opencode_4py to [PROJECT_NAME] in for_testing/.

Reference: plans/archive/TARGET_PROJECT_SYNC_PLAN.md

Steps:
1. Analyze for_testing/[PROJECT_NAME]/ structure
2. Identify opencode_4py features to integrate
3. Create integration plan specific to project
4. Implement integration maintaining project compatibility
5. Test integration in for_testing environment
6. Document integration steps
```

**Example**:
```
Start integration of opencode_4py to ComfyUI in for_testing/.

Reference: plans/archive/TARGET_PROJECT_SYNC_PLAN.md

Steps:
1. Analyze for_testing/ComfyUI/ structure
2. Identify opencode_4py features to integrate
3. Create integration plan specific to project
4. Implement integration maintaining project compatibility
5. Test integration in for_testing environment
6. Document integration steps
```

---

### 3. Sync Code Changes to Project

**Purpose**: Apply opencode_4py main code changes to a project in `for_testing/`

**Prompt**:
```
Sync opencode_4py code changes to [PROJECT_NAME] in for_testing/.

Reference: plans/archive/TARGET_PROJECT_SYNC_PLAN.md

Steps:
1. Identify recent opencode_4py changes to sync
2. Check for_testing/[PROJECT_NAME]/ for conflicts
3. Apply changes maintaining project-specific customizations
4. Run project tests to verify sync
5. Update project documentation if needed
6. Report sync status
```

**Example**:
```
Sync opencode_4py code changes to ComfyUI in for_testing/.

Reference: plans/archive/TARGET_PROJECT_SYNC_PLAN.md

Steps:
1. Identify recent opencode_4py changes to sync
2. Check for_testing/ComfyUI/ for conflicts
3. Apply changes maintaining project-specific customizations
4. Run project tests to verify sync
5. Update project documentation if needed
6. Report sync status
```

---

### 4. Begin Testing

**Purpose**: Start testing opencode_4py code changes (unit tests, integration tests)

**Prompt**:
```
Begin testing [FEATURE/COMPONENT] code changes to opencode_4py.

Reference: plans/TESTING_PLAN.md

Steps:
1. Review existing tests in src/opencode/tests/
2. Create test cases for [FEATURE/COMPONENT]
3. Run tests: pytest src/opencode/tests/
4. Document results and coverage
5. Report issues and recommendations
```

**Example**:
```
Begin testing RAG pipeline code changes to opencode_4py.

Reference: plans/TESTING_PLAN.md

Steps:
1. Review existing tests in src/opencode/tests/
2. Create test cases for RAG pipeline
3. Run tests: pytest src/opencode/tests/
4. Document results and coverage
5. Report issues and recommendations
```

---

### 5. Sync Code Changes to GitHub

**Purpose**: Update GitHub locally and remotely (both main project and target repos).

**CLI Commands** (manual):
```bash
# Navigate to the opencode project
cd src/opencode



# Stage and commit changes
git add -A
git commit -m "Your commit message"

# Push to opencode_4py
git push origin main

# Force push to comfyui repo (syncs with opencode_4py)
git push comfyui main --force
```

**Using opencode CLI**:
```bash
# Check configured repositories
opencode github repos

# Push to all repos
opencode github push-all -m "Your message"

# Push to specific repos
opencode github push-all -r "opencode_4py" -m "Update"

# Sync to local target (like ComfyUI portable)
opencode github sync -t for_testing/as_dependency/ComfyUI_windows_portable -m "Sync update"

# Dry run (preview what would happen)
opencode github push-all --dry-run
```

**Prompt**:
```
Update GitHub repositories with latest changes.

Reference: plans/GITHUB_UPLOAD_PLAN.md

Steps:
1. Check configured repositories: opencode github repos
2. Stage and commit changes: opencode github push-all -m "Your message"
3. Verify push success for each repository
4. Report status for all repos
```

**Example** (push to all repos):
```
Update GitHub repositories with latest changes.

Reference: plans/GITHUB_UPLOAD_PLAN.md

Steps:
1. Check configured repositories: opencode github repos
2. Push to all repos: opencode github push-all -m "Feature update"
3. Verify push success for each repository
4. Report status for all repos
```

**Example** (sync to local target):
```
Sync opencode_4py to local ComfyUI portable project.

Reference: plans/GITHUB_UPLOAD_PLAN.md

Steps:
1. Sync to local target: opencode github sync -t for_testing/as_dependency/ComfyUI_windows_portable -m "Sync update"
2. Verify sync completed
3. Optionally push to remote
```

**Example** (dry run):
```
Preview what would be pushed to GitHub.

Reference: plans/GITHUB_UPLOAD_PLAN.md

Steps:
1. Dry run: opencode github push-all --dry-run
2. Review what would happen
3. Confirm or adjust as needed
```

---

## Quick Reference Table

| Command | Source | Target | Reference Plan |
|---------|--------|--------|----------------|
| **Merge** | `merge_projects/[PROJECT]` | `opencode_4py` | [MERGE_INTEGRATION_PLAN.md](MERGE_INTEGRATION_PLAN.md) |
| **Integrate** | `opencode_4py` | `for_testing/[PROJECT]` | [TARGET_PROJECT_SYNC_PLAN.md](archive/TARGET_PROJECT_SYNC_PLAN.md) |
| **Sync** | `opencode_4py` (changes) | `for_testing/[PROJECT]` | [TARGET_PROJECT_SYNC_PLAN.md](archive/TARGET_PROJECT_SYNC_PLAN.md) |
| **Test** | `opencode_4py` (code) | `src/opencode/tests/` | [TESTING_PLAN.md](TESTING_PLAN.md) |
| **GitHub Push** | `opencode_4py` | GitHub repos | [GITHUB_UPLOAD_PLAN.md](GITHUB_UPLOAD_PLAN.md) |
| **Review** | `opencode_4py` (all) | Improvement recommendations | [COMPREHENSIVE_PROJECT_REVIEW_PLAN.md](COMPREHENSIVE_PROJECT_REVIEW_PLAN.md) |

---

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Quick Start Workflows                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  MERGE (external → opencode_4py)                                │
│  ┌──────────────────┐      ┌──────────────────┐                 │
│  │ merge_projects/  │ ───▶ │   opencode_4py   │                 │
│  │ [PROJECT_NAME]   │      │   (main code)    │                 │
│  └──────────────────┘      └──────────────────┘                 │
│                                                                  │
│  INTEGRATE (opencode_4py → external)                            │
│  ┌──────────────────┐      ┌──────────────────┐                 │
│  │   opencode_4py   │ ───▶ │  for_testing/    │                 │
│  │   (main code)    │      │ [PROJECT_NAME]   │                 │
│  └──────────────────┘      └──────────────────┘                 │
│                                                                  │
│  SYNC (opencode_4py changes → external)                         │
│  ┌──────────────────┐      ┌──────────────────┐                 │
│  │   opencode_4py   │ ───▶ │  for_testing/    │                 │
│  │   (changes)      │      │ [PROJECT_NAME]   │                 │
│  └──────────────────┘      └──────────────────┘                 │
│                                                                  │
│  GITHUB PUSH (opencode_4py → GitHub)                           │
│  ┌──────────────────┐      ┌──────────────────┐                 │
│  │   opencode_4py   │ ───▶ │  GitHub repos   │                 │
│  │   (local)        │      │ (multiple)       │                 │
│  └──────────────────┘      └──────────────────┘                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Related Plans

- [MERGE_INTEGRATION_PLAN.md](MERGE_INTEGRATION_PLAN.md) - Detailed merge planning
- [TARGET_PROJECT_SYNC_PLAN.md](archive/TARGET_PROJECT_SYNC_PLAN.md) - Sync and integration details
- [FOR_TESTING_PLAN.md](archive/FOR_TESTING_PLAN.md) - Testing infrastructure
- [CODE_IMPROVEMENT_PLAN.md](CODE_IMPROVEMENT_PLAN.md) - Code quality standards
- [TESTING_PLAN.md](TESTING_PLAN.md) - Testing strategy

---

*Last updated: 2026-02-27*

## Change Log

| Date | Change |
|------|--------|
| 2026-02-27 | Added manual git commands for GitHub sync |

| 2026-02-24 | Initial creation - Quick Start Commands guide |
