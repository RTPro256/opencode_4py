# ERR-013: Session and Log Storage Location

## Metadata
- **Error ID**: ERR-013
- **Category**: Configuration
- **Severity**: Low
- **Status**: Fixed
- **Date Encountered**: 2026-02-23
- **Related Errors**: None

## Symptom
Sessions and logs were being saved to user's home directory instead of the target project's docs folder.

## Root Cause
The default `data_dir` was set to `~/.local/share/opencode`, which is not project-specific.

## Fix
Modified `Config.load()` to set `data_dir` to `{project_dir}/docs/opencode` when a project directory is provided:

```python
# In config.py
if project_dir:
    config.data_dir = project_dir / "docs" / "opencode"
```

## Session Filename Format
Sessions are now saved with datetime in the filename:
```
session_YYYY-MM-DD_HH-MM-SS_{short_id}.json
```

## Log Filename Format
Logs are saved with datetime in the filename:
```
opencode_YYYY-MM-DD_HH-MM-SS.log
```

## Storage Structure
```
{project_dir}/
├── docs/
│   └── opencode/
│       ├── sessions/
│       │   └── session_2026-02-23_12-30-45_abc12345.json
│       └── logs/
│           └── opencode_2026-02-23_12-30-45.log
└── plans/
    └── (target-specific plans go here)
```

## Verification
```bash
# Check where sessions are stored
ls -la docs/opencode/sessions/

# Check where logs are stored
ls -la docs/opencode/logs/
```

## Lesson Learned
When integrating into a target project, all generated files (sessions, logs, etc.) should be stored in the target project's directory structure, not in user's home directory. This keeps everything self-contained and makes it easier to manage, backup, and troubleshoot.

## Prevention
- Always set project-specific paths for data storage
- Document the storage structure in integration guides
- Provide configuration options for custom storage locations
