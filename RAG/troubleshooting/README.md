# Troubleshooting RAG

This RAG (Retrieval-Augmented Generation) index is for **troubleshooting OpenCode_4py integration issues**.

## Purpose

The debugging agent uses this RAG to:
- Quickly find solutions to known integration errors
- Retrieve relevant troubleshooting patterns
- Access error diagnosis workflows
- Reference fix implementations

## Directory Structure

```
RAG/troubleshooting/
├── README.md                    # This file
├── errors/                      # Individual error documents
│   ├── ERR-001-cli-command-structure.md
│   ├── ERR-002-sqlalchemy-syntax.md
│   ├── ERR-003-ai-provider-availability.md
│   ├── ERR-004-missing-preflight-checks.md
│   ├── ERR-005-web-framework-response-types.md
│   ├── ERR-006-dependency-version-warnings.md
│   ├── ERR-007-wrong-provider-class.md
│   ├── ERR-008-single-line-input-widget.md
│   ├── ERR-009-wrong-provider-method-name.md
│   ├── ERR-010-async-generator-await.md
│   ├── ERR-011-runtime-logging-silent-failures.md
│   ├── ERR-012-missing-parameter-init.md
│   ├── ERR-013-session-log-storage-location.md
│   ├── ERR-014-reactive-property-watch-missing.md
│   ├── ERR-015-installed-vs-source-mismatch.md
│   ├── ERR-016-mutation-observer-button.md
│   └── ERR-017-comfyui-button-selector.md
├── patterns/                    # Troubleshooting patterns
│   ├── PATTERN-001-tui-stall-diagnosis.md
│   ├── PATTERN-002-provider-connection.md
│   └── PATTERN-003-integration-verification.md
└── workflows/                   # Diagnosis workflows
    ├── WORKFLOW-001-tui-troubleshooting.md
    └── WORKFLOW-002-integration-troubleshooting.md
```

## Error Document Format

Each error document follows this structure:

```markdown
# ERR-XXX: [Error Title]

## Symptoms
[What the user observes]

## Root Cause
[Technical explanation of why this happens]

## Diagnosis
[How to identify this error]

## Fix
[Step-by-step solution]

## Code Examples
[Before/After code snippets]

## Related Errors
[Links to related error documents]

## Source
[Where this error was first documented]
```

## Usage

```bash
# Query the troubleshooting RAG
opencode rag query --agent troubleshooting "TUI stalls at Thinking"

# Add new error document
opencode rag add --agent troubleshooting ./errors/ERR-018-new-error.md

# Rebuild the RAG index
opencode rag rebuild --agent troubleshooting
```

## Integration with Debugging Agent

The debugging agent should:

1. **Query this RAG first** when encountering an error
2. **Use semantic search** to find similar errors by symptom
3. **Follow the diagnosis workflow** to confirm the error
4. **Apply the fix** from the error document
5. **Add new errors** when discovering undocumented issues

## Index Status

- **Created**: Not yet created
- **Documents**: 17 error documents ready
- **Last Updated**: 2026-02-23

Run `opencode rag create --agent troubleshooting` to initialize this RAG.
