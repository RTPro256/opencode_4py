# ERR-016: MutationObserver for Dynamic Button Positioning

**Severity:** MEDIUM
**Category:** Web Integration
**First Documented:** 2026-02-23
**Source:** ComfyUI Integration

## Symptoms

- Custom button not appearing next to target button in web interface
- Console shows "Button added to menu (fallback)" instead of correct position
- Button appears in wrong location or not at all

## Root Cause

The target button is added dynamically by another extension/script after your extension loads. When your code tries to find the target button, it doesn't exist yet in the DOM.

## Diagnosis

1. Check browser console for button positioning messages
2. Inspect DOM to see when target button appears
3. Check if target button has specific class/attributes when it loads

## Fix

Use `MutationObserver` to wait for the target button to appear:

```javascript
// Try immediately first
if (insertButtonNextToManager()) {
    return;
}

// If not found, use MutationObserver to wait for the target button
const observer = new MutationObserver((mutations, obs) => {
    if (insertButtonNextToManager()) {
        obs.disconnect();
    }
});

// Start observing the document body for added nodes
observer.observe(document.body, {
    childList: true,
    subtree: true
});

// Set timeout as fallback
setTimeout(() => {
    observer.disconnect();
    // Final fallback attempt
}, 10000);
```

## Code Example

**Before (Incorrect):**
```javascript
// This runs before Manager button exists
const managerButton = document.querySelector('button');
if (managerButton) {
    managerButton.parentElement.insertBefore(myButton, managerButton);
}
```

**After (Correct):**
```javascript
function insertButtonNextToManager() {
    // Check if already inserted
    if (document.getElementById("my-button")) {
        return true;
    }
    
    // Find target button
    let targetButton = document.querySelector('button[title="Target Button"]');
    
    if (targetButton && targetButton.parentElement) {
        const myButton = createMyButton();
        targetButton.parentElement.insertBefore(myButton, targetButton);
        return true;
    }
    
    return false;
}

// Use MutationObserver to wait for target
const observer = new MutationObserver((mutations, obs) => {
    if (insertButtonNextToManager()) {
        obs.disconnect();
    }
});

observer.observe(document.body, { childList: true, subtree: true });
```

## Technical Explanation

| Concept | Description |
|---------|-------------|
| **MutationObserver** | API to watch for DOM changes |
| **childList** | Watch for added/removed children |
| **subtree** | Watch all descendants, not just direct children |
| **disconnect()** | Stop observing when done |

## Related Errors

- [ERR-017: ComfyUI Button Selector Specificity](ERR-017-comfyui-button-selector.md) - Finding the right button

## Prevention

1. Always use MutationObserver for dynamic content
2. Set a timeout fallback for cases where target never appears
3. Check if button already exists before observing
4. Use specific selectors that match actual DOM structure
