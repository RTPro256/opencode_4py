# Integrated App Documentation Plan

> **Perspective Shift:** When opencode_4py is integrated into an application, it becomes "self" within that app's context. This plan defines how integrated apps document themselves for opencode_4py's plans and agents.

## Executive Summary

When opencode_4py is integrated into a host application, it needs to understand that application's context. The `{APP_NAME}_INDEX.md` document serves as the "self-knowledge" file that opencode_4py uses to understand its host environment.

## Key Concepts

### 1. Self Perspective

When opencode_4py runs inside an integrated app:
- opencode_4py becomes "self" - it is part of the app, not external to it
- The host app's goals become opencode_4py's goals
- The host app's constraints become opencode_4py's constraints
- The host app's users become opencode_4py's users

### 2. {APP_NAME}_INDEX.md

Each integrated app should have an index document that provides:

| Section | Purpose | Content |
|---------|---------|---------|
| **App Overview** | What is this app? | Name, purpose, target users |
| **Architecture** | How is it built? | Tech stack, key directories, entry points |
| **Integration Points** | Where is opencode_4py? | Site-packages location, config files |
| **Key Files** | What matters? | Important files for AI to understand |
| **Workflows** | How to work? | Common tasks, development patterns |
| **Constraints** | What to avoid? | Project-specific rules, limitations |

### 3. Documentation Location

```
{integrated_app}/
├── {APP_NAME}_INDEX.md          # Self-knowledge document (project root)
├── opencode.toml                 # opencode_4py configuration
├── python_embeded/
│   └── Lib/site-packages/opencode/
│       ├── README.md             # opencode_4py README (for AI context)
│       ├── MISSION.md            # opencode_4py MISSION (for AI context)
│       └── RAG/troubleshooting/  # Error patterns (for AI context)
└── docs/
    └── opencode/
        ├── sessions/             # Chat sessions
        └── logs/                 # Debug logs
```

## {APP_NAME}_INDEX.md Template

```markdown
# {APP_NAME} Index

> **Self-Knowledge Document for opencode_4py Integration**

## App Overview

- **Name:** {App Name}
- **Purpose:** {What does this app do?}
- **Target Users:** {Who uses this app?}
- **Repository:** {GitHub URL if applicable}

## Architecture

### Tech Stack
- **Language:** Python 3.x
- **Framework:** {Framework name}
- **Key Dependencies:** {List major dependencies}

### Directory Structure
```
{APP_NAME}/
├── {dir1}/           # {Purpose}
├── {dir2}/           # {Purpose}
└── ...
```

### Entry Points
- **Main:** `{file_path}` - {Description}
- **Config:** `{file_path}` - {Description}

## opencode_4py Integration

### Installation Location
- **Site-packages:** `python_embeded/Lib/site-packages/opencode/`
- **Config:** `opencode.toml` (project root)

### Configuration
- **Default Model:** {model_name}
- **Provider:** {provider_name}
- **Special Settings:** {Any project-specific settings}

## Key Files for AI Context

| File | Purpose | When to Reference |
|------|---------|-------------------|
| `{file}` | {purpose} | {when} |

## Common Workflows

### {Workflow 1}
1. {Step 1}
2. {Step 2}
3. {Step 3}

### {Workflow 2}
1. {Step 1}
2. {Step 2}

## Constraints and Rules

### Must Do
- {Rule 1}
- {Rule 2}

### Must Not Do
- {Prohibition 1}
- {Prohibition 2}

## Related Documentation

- [opencode_4py README](python_embeded/Lib/site-packages/opencode/README.md)
- [opencode_4py MISSION](python_embeded/Lib/site-packages/opencode/MISSION.md)
- [Troubleshooting RAG](python_embeded/Lib/site-packages/opencode/RAG/troubleshooting/README.md)
```

## Integration with opencode_4py README

The opencode_4py README.md should document the INDEX.md convention:

```markdown
## Integrated App Documentation

When opencode_4py is integrated into a host application, the host app should provide a `{APP_NAME}_INDEX.md` file at its root. This document serves as "self-knowledge" for opencode_4py when running within that app.

### For App Developers

If you're integrating opencode_4py into your app:

1. Create `{APP_NAME}_INDEX.md` at your project root
2. Document your app's architecture, key files, and workflows
3. Include any constraints or rules for AI assistance
4. Reference the opencode_4py README and MISSION for AI context

### For AI Agents

When operating within an integrated app:
- Read the `{APP_NAME}_INDEX.md` first to understand the host context
- Treat the host app's goals as your own goals
- Respect the host app's constraints and rules
- Use the troubleshooting RAG for error resolution
```

## Benefits

1. **Context Awareness**: opencode_4py understands its host environment
2. **Consistent Behavior**: AI respects project-specific rules
3. **Efficient Onboarding**: New developers get AI that already knows the project
4. **Self-Documenting**: The INDEX.md serves as project documentation too

## Implementation Steps

1. [ ] Add INDEX.md documentation to opencode_4py README.md
2. [ ] Create COMFYUI_INDEX.md for ComfyUI_windows_portable
3. [ ] Update TARGET_PROJECT_SYNC_PLAN.md to include INDEX.md sync
4. [ ] Create template in `for_testing/as_dependency/templates/`

---

*Created: 2026-02-25*
*Related: [TARGET_PROJECT_SYNC_PLAN.md](TARGET_PROJECT_SYNC_PLAN.md)*
