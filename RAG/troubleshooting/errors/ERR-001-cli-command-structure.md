# ERR-001: CLI Command Structure

## Metadata
- **Error ID**: ERR-001
- **Category**: Integration
- **Severity**: Low
- **Status**: Fixed
- **Date Encountered**: 2026-02-23
- **Related Errors**: None

## Symptom
Integration launch script fails with "unknown argument" error.

## Root Cause
The integration used `--tui` flag which doesn't exist in the CLI.

## Incorrect Code
```batch
.\python_embeded\python.exe -m opencode --tui
```

## Fix
Use `python -m opencode run` instead:
```batch
.\python_embeded\python.exe -m opencode run
```

## Verification
```bash
python -m opencode --help
python -m opencode run --help
```

## Lesson Learned
Always verify CLI structure with `--help` before writing launch scripts.

## Prevention
- Run `--help` on all commands before using them
- Document the correct CLI structure in integration guides
- Add pre-flight checks to verify command structure
