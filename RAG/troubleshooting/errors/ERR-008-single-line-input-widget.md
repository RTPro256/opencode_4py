# ERR-008: Single-line Input Widget

## Metadata
- **Error ID**: ERR-008
- **Category**: UI/UX
- **Severity**: Medium
- **Status**: Fixed
- **Date Encountered**: 2026-02-23
- **Related Errors**: None

## Symptom
User feedback: "The opencode_4py prompt does not accept multi-line PASTE command."

## Root Cause
TUI used `Input` widget which doesn't support multi-line paste. The `Input` widget in Textual is designed for single-line text entry.

## Incorrect Code
```python
from textual.widgets import Input

class InputArea(Container):
    def compose(self) -> ComposeResult:
        yield Input(placeholder="Type your message...")
```

## Fix
Replace `Input` with `TextArea` widget, add Send button, Enter to send/Shift+Enter for new line:

```python
from textual.widgets import TextArea, Button

class InputArea(Container):
    def compose(self) -> ComposeResult:
        yield TextArea(id="message-input", classes="message-input")
        yield Button("Send", id="send-button", variant="primary")
    
    def on_key(self, event: Key) -> None:
        if event.key == "enter" and not event.shift:
            # Send message
            self.send_message()
            event.prevent_default()
        # Shift+Enter allows new line (default behavior)
```

## Verification
1. Paste multi-line text into input area
2. Verify all lines appear
3. Test Enter sends message
4. Test Shift+Enter creates new line

## Lesson Learned
Chat interfaces need multi-line input support (TextArea, not Input).

## Prevention
- Use TextArea for any input that might need multiple lines
- Test paste functionality during development
- Consider user expectations from other chat applications
