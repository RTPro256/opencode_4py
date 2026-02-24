# ERR-002: SQLAlchemy Syntax

## Metadata
- **Error ID**: ERR-002
- **Category**: Dependency
- **Severity**: Low
- **Status**: Fixed
- **Date Encountered**: 2026-02-23
- **Related Errors**: None

## Symptom
Warning message appears: `SAWarning: Can't validate argument 'on_delete'`

## Root Cause
The `on_delete` parameter should be `ondelete` in SQLAlchemy 2.x.

## Incorrect Code
```python
ForeignKey("sessions.id", on_delete="CASCADE")
```

## Fix
Use `ondelete` instead of `on_delete`:
```python
ForeignKey("sessions.id", ondelete="CASCADE")
```

## Verification
```bash
python -c "import sqlalchemy; print(sqlalchemy.__version__)"
```

## Lesson Learned
Verify ORM syntax matches the installed version.

## Prevention
- Check SQLAlchemy version before using syntax
- Use version-specific documentation
- Add linter rules for SQLAlchemy syntax
