# Bug Detected RAG

This RAG index is automatically populated when opencode_4py detects bugs, errors, or failures.

## Purpose

When opencode_4py encounters an error during:
- Test execution
- Linting/type checking
- Runtime exceptions
- Import errors

The error details are automatically added to this RAG for:
1. Pattern recognition across similar errors
2. Solution retrieval from past fixes
3. Automatic troubleshooting suggestions

## Auto-Detection Triggers

| Trigger | Description | Action |
|---------|-------------|--------|
| `test_failure` | pytest test fails | Extract error message, stack trace |
| `lint_error` | ruff/mypy error | Extract error code, location |
| `runtime_exception` | Unhandled exception | Extract exception type, message |
| `type_error` | Type mismatch | Extract expected vs actual types |
| `import_error` | Module not found | Extract missing module name |

## Usage

```bash
# Query detected bugs
opencode rag query --bug "ModuleNotFoundError"

# Get similar past errors
opencode rag query --bug "similar to current error"

# Auto-query when error detected (automatic)
# opencode automatically queries this RAG when an error occurs
```

## Generated Files

- `bug_detected-RAG/` - Vector index of all detected bugs
- `errors/` - Individual error records
  - `ERR-{timestamp}-{hash}.md` - Error details
- `solutions/` - Linked solutions
  - `SOL-{err_hash}.md` - Solution for specific error

## Error Record Format

```markdown
# Error: {error_type}

## Detected
- Timestamp: {iso_timestamp}
- Location: {file}:{line}
- Trigger: {detection_trigger}

## Error Details
```
{full_error_message}
```

## Stack Trace
```
{stack_trace}
```

## Context
- Command: {command_that_caused_error}
- Working Directory: {cwd}
- Python Version: {version}

## Resolution Status
- [ ] Not resolved
- [ ] In progress
- [ ] Resolved

## Solution (if resolved)
{solution_description}
```

## Integration with Troubleshooting

This RAG integrates with:
- [`RAG/troubleshooting/`](../troubleshooting/) - Error patterns and solutions
- [`RAG/agent_troubleshooting/`](../agent_troubleshooting/) - Agent-specific troubleshooting
