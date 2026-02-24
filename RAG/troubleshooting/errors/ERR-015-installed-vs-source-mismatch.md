# ERR-015: Installed vs Source Code Mismatch

**Severity:** HIGH
**Category:** Deployment
**First Documented:** 2026-02-23
**Source:** ComfyUI Integration

## Symptoms

- Fixes made to source code (`src/opencode/`) don't appear in running application
- After fixing code, the same error persists when running the application
- Changes to files in the repository don't affect the installed package behavior

## Root Cause

The application runs from the installed location (`site-packages/opencode/`), not from the source code directory. Changes to source files don't automatically update the installed version.

## Diagnosis

1. Check where Python is loading the module from:
   ```python
   import opencode
   print(opencode.__file__)
   ```
2. Compare with source code location
3. If paths differ, the installed version is being used

## Fix

**Option 1:** Apply fixes directly to installed location
```
for_testing/as_dependency/ComfyUI_windows_portable/python_embeded/Lib/site-packages/opencode/
```

**Option 2:** Reinstall the package after source changes
```bash
# For editable install (changes reflect immediately)
pip install -e .

# For regular install (requires reinstall after changes)
pip install .
```

**Option 3:** Use PYTHONPATH to point to source
```bash
set PYTHONPATH=%~dp0src\opencode\src
```

## Code Example

**Finding the installed location:**
```python
# In Python
import opencode.tui.app as app_module
print(f"Loaded from: {app_module.__file__}")
# Output: C:\...\site-packages\opencode\tui\app.py
```

**For ComfyUI integration:**
```batch
REM The installed location is:
set INSTALLED_PATH=%~dp0python_embeded\Lib\site-packages\opencode

REM Apply fixes to files in this location, not in src/opencode/
```

## Technical Explanation

| Install Type | Source Location | Changes Reflect |
|--------------|-----------------|-----------------|
| Regular `pip install .` | `site-packages/` | After reinstall |
| Editable `pip install -e .` | Source directory | Immediately |
| PYTHONPATH override | Source directory | Immediately |
| Direct copy | `site-packages/` | After restart |

## Related Errors

- [ERR-014: Reactive Property Watch Missing](ERR-014-reactive-property-watch-missing.md) - Fix must be applied to correct location

## Prevention

1. Know which install type you're using
2. For development, use editable install (`pip install -e .`)
3. For integration testing, apply fixes to installed location
4. Document the installed path in integration notes
