# ERR-006: Dependency Version Warnings

## Metadata
- **Error ID**: ERR-006
- **Category**: Dependency
- **Severity**: Low
- **Status**: Fixed
- **Date Encountered**: 2026-02-23
- **Related Errors**: None

## Symptom
Warning: `RequestsDependencyWarning: urllib3 (2.6.3) doesn't match a supported version!`

## Root Cause
urllib3/chardet versions newer than what requests was tested with.

## Fix
Suppress with `-W ignore` Python flag if functionality is not affected:

```batch
.\python_embeded\python.exe -W ignore -m opencode run
```

Or pin the dependency versions in requirements.txt:
```
urllib3>=1.26.0,<2.0.0
chardet>=3.0.0,<5.0.0
```

## Verification
```bash
# Check if warning affects functionality
python -c "import requests; print(requests.__version__)"
python -c "import urllib3; print(urllib3.__version__)"
```

## Lesson Learned
Version warnings often don't affect functionality; suppress if safe.

## Prevention
- Test with warning enabled first to verify functionality
- Document known-safe version combinations
- Use dependency pinning for production deployments
