# File System Sandboxing

## Overview

When opencode_4py is integrated as a dependency into another application (like ComfyUI), file system sandboxing restricts file access to the target project directory. This ensures that opencode_4py cannot access or modify files outside the designated project folder without explicit user permission.

## How It Works

### Sandbox Initialization

The sandbox is initialized when the TUI application starts in integration mode:

```python
from opencode.core.sandbox import initialize_sandbox, AccessDecision, AccessRequest

# Initialize sandbox with allowed root directory
initialize_sandbox(
    allowed_roots=[Path("/path/to/project")],
    permission_callback=permission_callback,
    strict_mode=True,
)
```

### Access Types

The sandbox supports four types of file access:

| Access Type | Description |
|-------------|-------------|
| `READ` | Reading file contents |
| `WRITE` | Writing or modifying files |
| `DELETE` | Deleting files |
| `EXECUTE` | Executing files or commands |

### Permission Callback

When a file access request is made outside the allowed directories, the permission callback is invoked:

```python
def permission_callback(request: AccessRequest) -> AccessDecision:
    """
    Handle permission request for external file access.
    
    Args:
        request: AccessRequest with path, access_type, and reason
        
    Returns:
        AccessDecision: ALLOW, DENY, ALLOW_ONCE, or DENY_ONCE
    """
    # Show dialog to user, log request, etc.
    return AccessDecision.DENY
```

### Access Decisions

| Decision | Effect |
|----------|--------|
| `ALLOW` | Permanently allow access to this path |
| `DENY` | Permanently deny access to this path |
| `ALLOW_ONCE` | Allow this single access request |
| `DENY_ONCE` | Deny this single access request |

## Integration with File Tools

All file tools (`ReadTool`, `WriteTool`, `EditTool`, `GlobTool`, `GrepTool`) automatically check the sandbox before accessing files:

```python
# In file_tools.py
from opencode.core.sandbox import (
    AccessType,
    check_file_access,
    is_sandbox_active,
)

async def execute(self, file_path: str, ...):
    path = self.working_directory / file_path
    path = path.resolve()
    
    # Check sandbox if active (integration mode)
    if is_sandbox_active():
        allowed, reason = check_file_access(path, AccessType.READ)
        if not allowed:
            return ToolResult.err(reason or "Access denied: sandbox restriction")
    
    # Continue with file operation...
```

## CLI Usage

### Standard Mode (No Sandboxing)

```bash
opencode run
opencode run --directory /path/to/project
```

### Integration Mode (With Sandboxing)

```bash
opencode run --sandbox-root /path/to/project
```

When `--sandbox-root` is specified:
- File access is restricted to the specified directory
- Access outside the directory triggers the permission callback
- Strict mode denies access by default

## ComfyUI Integration

In the ComfyUI integration, the sandbox is automatically configured:

```python
# In ComfyUI-OpenCode_4py/__init__.py
def launch_opencode_4py():
    comfyui_path = os.path.join(base_path, "ComfyUI")
    
    subprocess.Popen([
        python_exe, "-m", "opencode", "run",
        "--sandbox-root", comfyui_path
    ], ...)
```

This ensures opencode_4py can only access files within the ComfyUI directory.

## Security Considerations

### Path Traversal Prevention

The sandbox prevents path traversal attacks:

```python
# These are blocked:
../../../etc/passwd
..\..\..\Windows\System32
/symlink/to/outside/directory
```

### Symlink Handling

Symlinks are resolved before checking access:

```python
path = path.resolve()  # Resolves symlinks
allowed, reason = check_file_access(path, AccessType.READ)
```

### Strict Mode

In strict mode (default for integration):
- Access is denied by default if no callback is provided
- All access attempts are logged
- Permission decisions are cached for performance

## API Reference

### `initialize_sandbox()`

```python
def initialize_sandbox(
    allowed_roots: List[Path],
    permission_callback: Optional[Callable[[AccessRequest], AccessDecision]] = None,
    strict_mode: bool = True,
) -> FileSandbox:
    """
    Initialize the global file sandbox.
    
    Args:
        allowed_roots: List of root directories that are always allowed
        permission_callback: Callback for requesting permission for external access
        strict_mode: If True, deny access by default. If False, allow with warning.
    
    Returns:
        The initialized FileSandbox instance
    """
```

### `check_file_access()`

```python
def check_file_access(
    path: Path,
    access_type: AccessType
) -> tuple[bool, Optional[str]]:
    """
    Check if file access is allowed.
    
    Args:
        path: Path to check
        access_type: Type of access being requested
        
    Returns:
        Tuple of (is_allowed, reason_if_denied)
    """
```

### `is_sandbox_active()`

```python
def is_sandbox_active() -> bool:
    """Check if sandboxing is active."""
```

### `get_sandbox()`

```python
def get_sandbox() -> Optional[FileSandbox]:
    """Get the global file sandbox instance."""
```

## Best Practices

1. **Always use `--sandbox-root` in integration mode** - This ensures file system isolation
2. **Implement a user-facing permission dialog** - Allow users to approve/deny external access
3. **Log all access attempts** - Useful for debugging and security auditing
4. **Use strict mode** - Deny by default for better security
5. **Test with symlinks** - Ensure symlink resolution works correctly

## Example: Custom Permission Dialog

```python
from textual.widgets import ModalScreen, Button, Static
from textual.containers import Vertical

class PermissionDialog(ModalScreen):
    """Dialog for requesting file access permission."""
    
    def __init__(self, request: AccessRequest):
        super().__init__()
        self.request = request
    
    def compose(self):
        yield Vertical(
            Static(f"File Access Request"),
            Static(f"Path: {self.request.path}"),
            Static(f"Access Type: {self.request.access_type.value}"),
            Static(f"Reason: {self.request.reason}"),
            Button("Allow", id="allow"),
            Button("Deny", id="deny"),
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "allow":
            self.dismiss(AccessDecision.ALLOW)
        else:
            self.dismiss(AccessDecision.DENY)
```

## Troubleshooting

### "Access denied: sandbox restriction"

This error occurs when:
1. Sandbox is active and the path is outside allowed directories
2. The permission callback denied access
3. Strict mode is enabled and no callback is configured

**Solution**: Ensure the file is within the sandbox root, or implement a permission callback to request user approval.

### Sandbox not activating

Check that:
1. `--sandbox-root` is passed to the `run` command
2. The path exists and is accessible
3. `initialize_sandbox()` is called before any file operations

### Performance impact

The sandbox has minimal performance impact:
- Permission decisions are cached
- Path resolution is done once per operation
- No network calls or external dependencies
