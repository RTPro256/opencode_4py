# ERR-017: ComfyUI Button Selector Specificity

**Severity:** MEDIUM
**Category:** Web Integration
**First Documented:** 2026-02-23
**Source:** ComfyUI Integration

## Symptoms

- JavaScript can't find the Manager button using generic selectors
- `document.querySelectorAll("button")` doesn't find the target button
- Button positioning code fails silently

## Root Cause

ComfyUI uses specific button structure with classes and attributes that generic selectors don't match. The Manager button has a specific HTML structure:

```html
<button title="ComfyUI Manager" aria-label="ComfyUI Manager" 
        class="comfyui-button comfyui-menu-mobile-collapse primary">
  <i class="mdi mdi-puzzle"></i>
  <span>Manager</span>
</button>
```

## Diagnosis

1. Open browser Developer Tools (F12)
2. Use Elements tab to inspect the target button
3. Note the exact classes, attributes, and structure
4. Test selectors in Console: `document.querySelector('your-selector')`

## Fix

Use specific selectors matching the actual HTML structure:

```javascript
// Method 1: Find by title attribute (most specific)
let managerButton = document.querySelector('button[title="ComfyUI Manager"]');

// Method 2: Find by aria-label
if (!managerButton) {
    managerButton = document.querySelector('button[aria-label="ComfyUI Manager"]');
}

// Method 3: Find by class and span text
if (!managerButton) {
    const comfyButtons = document.querySelectorAll("button.comfyui-button");
    for (const btn of comfyButtons) {
        const span = btn.querySelector("span");
        if (span && span.textContent.trim() === "Manager") {
            managerButton = btn;
            break;
        }
    }
}
```

## Code Example

**Before (Incorrect):**
```javascript
// Generic selector - may find wrong button or none
const buttons = document.querySelectorAll("button");
for (const btn of buttons) {
    if (btn.textContent && btn.textContent.includes("Manager")) {
        // This might match multiple buttons or wrong button
    }
}
```

**After (Correct):**
```javascript
// Specific selector matching actual DOM structure
let managerButton = document.querySelector('button[title="ComfyUI Manager"]');

if (managerButton && managerButton.parentElement) {
    const myButton = createMyButton();
    // Insert BEFORE the Manager button (to the left)
    managerButton.parentElement.insertBefore(myButton, managerButton);
}
```

## Technical Explanation

| Selector Type | Example | Specificity |
|---------------|---------|-------------|
| Attribute | `button[title="X"]` | High |
| Class | `button.comfyui-button` | Medium |
| Text Content | `span:contains("X")` | Low |
| Generic | `button` | Very Low |

## Creating Matching Button Style

To match ComfyUI button style:

```javascript
const button = document.createElement("button");
button.title = "My Button";
button.setAttribute("aria-label", "My Button");
button.className = "comfyui-button comfyui-menu-mobile-collapse";

// Add icon
const icon = document.createElement("i");
icon.className = "mdi mdi-robot";

// Add text
const text = document.createElement("span");
text.textContent = "My Button";

button.appendChild(icon);
button.appendChild(text);
```

## Related Errors

- [ERR-016: MutationObserver for Button Positioning](ERR-016-mutation-observer-button.md) - Waiting for button to appear

## Prevention

1. Always inspect actual DOM structure before writing selectors
2. Use attribute selectors for unique identification
3. Test selectors in browser console before deploying
4. Have fallback selectors for robustness
