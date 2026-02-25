# OpenCode Session Storage

This directory contains chat session files for OpenCode when running with the `--project` flag pointing to the opencode_4py repository.

## Session File Format

**Filename Pattern:** `session_{YYYY-MM-DD_HH-MM-SS}_{short_id}.json`

**Example:** `session_2026-02-23_12-07-27_ea99a867.json`

## Session Storage Locations

| Setting | Session Location |
|---------|-----------------|
| `project_dir` configured in `opencode.toml` | `{project_dir}/docs/opencode/sessions/` |
| Running from project root | `./docs/sessions/` |
| No `project_dir` setting | `~/.local/share/opencode/sessions/` |

## TUI Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` | Save current session (auto-saved by default) |
| `Ctrl+N` | New session |
| `Ctrl+O` | Open session browser |

## Session File Structure

Session files are JSON format containing:

```json
{
  "id": "ea99a867-ff35-4b72-87fc-8913d5ed8465",
  "project_id": "opencode_4py",
  "title": "Auto-generated or user-specified title",
  "directory": "/path/to/project",
  "created_at": "2026-02-23T12:07:27",
  "updated_at": "2026-02-23T12:26:10",
  "messages": [
    {
      "id": "message-uuid",
      "role": "user",
      "content": [...],
      "created_at": "..."
    }
  ]
}
```

## Related Documentation

- [Main README - Session Management](../README.md#session-management)
- [FOR_TESTING_PLAN.md - Storage Location Rules](../../plans/FOR_TESTING_PLAN.md#storage-location-rules)
- [Session Module Source](../../src/opencode/src/opencode/core/session.py)
