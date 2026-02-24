# ERR-014: Reactive Property Watch Missing

**Severity:** CRITICAL
**Category:** UI Framework (Textual)
**First Documented:** 2026-02-23
**Source:** ComfyUI Integration

## Symptoms

- TUI displays "Thinking..." but AI response doesn't appear in the UI
- Log shows `Received X chunks, response length: Y` confirming response was received
- UI remains stuck showing "Thinking..." or initial placeholder text
- No error messages visible

## Root Cause

Textual reactive properties need a `watch_{property_name}()` method to trigger side effects when the property changes. Without this method, the property value changes but the UI doesn't re-render.

Additionally, the streaming code was setting `response_widget.content` instead of `response_widget.message_content`, so the reactive property wasn't being updated at all.

## Diagnosis

1. Check if log shows chunks being received but UI not updating
2. Look for reactive property without corresponding `watch_` method
3. Verify streaming code sets the correct property name

## Fix

**Step 1:** Add watch method to trigger re-render

```python
class MessageWidget(Static):
    message_content: reactive[str] = reactive("")
    
    def watch_message_content(self, content: str) -> None:
        """Called when message_content changes - triggers a re-render."""
        self.refresh()
```

**Step 2:** Ensure streaming code uses correct property name

```python
# In streaming loop
response_widget.message_content = full_response  # Correct property name
```

## Code Example

**Before (Incorrect):**
```python
class MessageWidget(Static):
    _content: reactive[str] = reactive("")  # Property with underscore
    
    def render(self) -> str:
        return f"[bold]{role_label}[/bold]\n\n{self._content}"

# Streaming code
response_widget.content = full_response  # Wrong property name!
```

**After (Correct):**
```python
class MessageWidget(Static):
    message_content: reactive[str] = reactive("")  # Renamed property
    
    def watch_message_content(self, content: str) -> None:
        """Called when message_content changes - triggers a re-render."""
        self.refresh()
    
    def render(self) -> str:
        return f"[bold]{role_label}[/bold]\n\n{self.message_content}"

# Streaming code
response_widget.message_content = full_response  # Correct property name
```

## Technical Explanation

| Textual Concept | Description |
|-----------------|-------------|
| **Reactive Property** | Property that triggers callbacks when changed |
| **watch_{name}()** | Method called automatically when property changes |
| **refresh()** | Triggers re-render of the widget |
| **Property Name** | Must match exactly between definition and usage |

## Related Errors

- [ERR-010: Async Generator Await Error](ERR-010-async-generator-await.md) - Similar symptom (TUI stall)
- [ERR-015: Installed vs Source Mismatch](ERR-015-installed-vs-source-mismatch.md) - Fix not appearing

## Prevention

1. Always add `watch_{property_name}()` method for reactive properties that need UI updates
2. Use consistent property names between definition and usage
3. Avoid naming conflicts with base class properties (e.g., `Static.content`)
