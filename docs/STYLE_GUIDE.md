# OpenCode Documentation Style Guide

This guide establishes consistent formatting and organization for OpenCode documentation.

---

## File Organization

### Directory Structure

```
docs/
├── INDEX.md              # Navigation hub (required)
├── README.md             # Main documentation entry
├── IMPLEMENTATION_STATUS.md
├── FEATURE_COVERAGE.md
├── TESTING_STATUS.md
└── [topic].md            # Topic-specific docs

plans/
├── [ACTIVE_PLAN].md      # Active planning documents
└── archive/
    └── [COMPLETED_PLAN].md

config/presets/
├── README.md
└── [preset].toml
```

### File Naming

- Use `UPPERCASE_WITH_UNDERSCORES.md` for documentation files
- Use `lowercase_with_underscores.md` for plans and guides
- Use descriptive names: `TESTING_PLAN.md` not `plan1.md`

---

## Markdown Formatting

### Headers

```markdown
# Document Title

> Brief description or purpose

---

## Section Title

### Subsection Title

#### Detail Level (use sparingly)
```

- Use ATX-style headers (`#` prefix)
- One H1 per document
- Header levels should not skip (H1 → H2 → H3)

### Tables

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
```

- Use tables for structured data, comparisons, status
- Align columns with dashes for readability

### Code Blocks

````markdown
```python
# Language-specific code
def example():
    pass
```

```bash
# Shell commands
pip install opencode-ai
```

```toml
# Configuration
[provider]
default = "anthropic"
```
````

- Always specify language for syntax highlighting
- Use inline code for: file paths, commands, variable names

### Links

```markdown
[Link text](path/to/file.md)
[External link](https://example.com)
[Reference to section](#section-anchor)
```

- Use relative paths for internal links
- Verify links exist before committing
- Update links when moving files

### Lists

```markdown
- Unordered item
- Another item
  - Nested item

1. Ordered item
2. Second item
```

- Use `-` for unordered lists
- Use `1.` for ordered lists (auto-numbered)

### Status Indicators

| Indicator | Meaning |
|-----------|---------|
| ✅ | Complete/Implemented |
| ❌ | Broken/Missing |
| ⚠️ | Warning/Caution |
| 🔄 | In Progress |
| 📋 | Planned |

---

## Document Types

### Plan Documents

Every plan should include:

1. **Header** - Title and objective
2. **Executive Summary** - Brief overview
3. **Phases/Sections** - Organized tasks
4. **Tasks** - Checkboxes for tracking
5. **Success Criteria** - Measurable outcomes
6. **Status** - Current state

```markdown
# Plan Title

> **Objective**: Brief description

---

## Executive Summary

Brief overview of the plan.

## Phase 1: [Name]

**Objective**: Phase goal

**Tasks**:
- [ ] Task 1
- [ ] Task 2

## Success Criteria

| Criteria | Status |
|----------|--------|
| Metric 1 | Target |

---

*Created: YYYY-MM-DD*
*Status: Draft/Active/Complete*
```

### Status Documents

Track implementation progress:

```markdown
## Component Status

| Component | Status | Notes |
|-----------|--------|-------|
| Feature A | ✅ Complete | Working |
| Feature B | 🔄 In Progress | 80% done |
| Feature C | 📋 Planned | Next sprint |
```

### Error Documentation

Follow the RAG troubleshooting format:

```markdown
# ERR-XXX: Error Title

## Symptoms

What the user observes.

## Root Cause

Why this happens.

## Solution

Step-by-step fix.

## Prevention

How to avoid in the future.
```

---

## Writing Guidelines

### Voice and Tone

- **Clear and concise** - Get to the point
- **Active voice** - "Run the command" not "The command should be run"
- **Present tense** - "This feature does X" not "This feature will do X"
- **Second person** - "You can..." not "Users can..."

### Terminology

| Term | Usage |
|------|-------|
| OpenCode | The project name (capitalized) |
| Provider | AI service provider (Anthropic, OpenAI, etc.) |
| TUI | Terminal User Interface |
| RAG | Retrieval-Augmented Generation |
| MCP | Model Context Protocol |

### Code Examples

- Include necessary imports
- Show expected output when helpful
- Keep examples minimal but complete
- Add comments for clarity

---

## Maintenance

### Regular Tasks

1. **Update INDEX.md** when adding new documents
2. **Archive completed plans** to `plans/archive/`
3. **Update status** in tracking documents
4. **Fix broken links** when reorganizing
5. **Review and update** outdated content

### Link Checking

Run the link checker before major changes:

```bash
python scripts/check_links.py
```

### Pre-commit

Documentation is checked by pre-commit hooks for:
- Markdown formatting
- Broken links (CI only)
- Spelling (optional)

---

*Last updated: 2026-02-24*
