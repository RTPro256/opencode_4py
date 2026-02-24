# PATTERN-003: Integration Verification

## Metadata
- **Pattern ID**: PATTERN-003
- **Category**: Verification Pattern
- **Applies To**: Post-integration verification

## Symptoms
- Integration appears complete but features don't work
- Code changes don't appear in running application
- UI elements not appearing as expected

## Verification Checklist

### Step 1: Verify Installation Location
```bash
# Check where the package is installed
python -c "import opencode; print(opencode.__file__)"

# Expected output should be in site-packages, not source directory
# Example: C:\...\python_embeded\Lib\site-packages\opencode\__init__.py
```

### Step 2: Verify Code Changes Applied
```bash
# If running from site-packages, changes must be applied there
# Check the installed version has your changes
grep -n "your_change" site-packages/opencode/tui/app.py
```

### Step 3: Verify CLI Commands
```bash
# Test CLI structure
python -m opencode --help
python -m opencode run --help

# Run application
python -m opencode run
```

### Step 4: Verify Web Integration (if applicable)
```bash
# Check custom node is loaded
# Look for log message in ComfyUI console:
# "Loading custom node: ComfyUI-OpenCode"

# Check JavaScript is loaded
# Open browser console, look for:
# "OpenCode custom node loaded"
```

### Step 5: Verify UI Elements
```bash
# For ComfyUI button:
# 1. Open ComfyUI in browser
# 2. Look for "🤖 OpenCode" button next to Manager button
# 3. Check browser console for JavaScript errors
```

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Changes not appearing | Editing source instead of installed | Apply to site-packages |
| Button not appearing | JavaScript selector wrong | Check DOM structure |
| CLI command not found | Wrong command syntax | Check `--help` output |
| Import errors | Missing dependencies | Run `pip install -e .` |

## Related Errors
- ERR-015: Installed vs Source Mismatch
- ERR-016: MutationObserver Button Positioning
- ERR-017: ComfyUI Button Selector Specificity
- ERR-001: CLI Command Structure

## Prevention
- Always verify installation location before making changes
- Use `pip install -e .` for development
- Test integration immediately after deployment
- Document expected behavior for verification
