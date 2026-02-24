# Onboarding Experience Review

> **Review Date**: 2026-02-24
> **Scope**: New user experience and getting started

---

## Executive Summary

The onboarding experience has been improved with configuration presets. An interactive tutorial is recommended as the next priority improvement.

---

## Current Onboarding Flow

### Step 1: Installation

```bash
pip install opencode-ai
```

**Status**: Simple and standard.

### Step 2: Configuration

Current options:
1. Set environment variables manually
2. Create `opencode.toml` manually
3. Use configuration presets (NEW)

**Complexity**: Medium (improved with presets)

### Step 3: First Run

```bash
opencode
```

**Status**: Launches TUI directly, no guided setup.

---

## Improvements Implemented

### Configuration Presets

Users can now quickly start with a pre-built configuration:

```bash
# For Claude users
cp config/presets/claude.toml ./opencode.toml
export ANTHROPIC_API_KEY=your-key
opencode

# For local users
cp config/presets/local.toml ./opencode.toml
ollama serve &
opencode
```

---

## Recommended Improvements

### High Priority: Interactive Tutorial

Create `opencode tutorial` command:

```
$ opencode tutorial

Welcome to OpenCode Tutorial!
============================

This tutorial will teach you how to use OpenCode effectively.

Lesson 1: Basic Chat
--------------------
Let's start with a simple conversation.

Try typing: "Hello! What can you help me with?"

[Input box here]

Great! OpenCode can help you with:
- Reading and writing code
- Running commands
- Searching your codebase
- And much more!

Press Enter to continue to Lesson 2...

Lesson 2: Reading Files
-----------------------
Let's read a file together.

Try typing: "Read the README.md file"

[Input box here]

You can read any file in your project this way.

Press Enter to continue...

Lesson 3: Making Changes
------------------------
Now let's make a simple change.

Try typing: "Add a comment to the main function"

[Input box here]

OpenCode will show you a diff before applying changes.

Press Enter to continue...

Congratulations!
----------------
You've completed the basic tutorial!

What would you like to do next?
1. Start a real session
2. Learn about agents (Tab to switch)
3. Learn about tools
4. Exit

[Selection]
```

### Medium Priority: First-Run Wizard

On first run, detect if configuration exists:

```
$ opencode

Welcome to OpenCode!
===================

It looks like this is your first time using OpenCode.

Would you like to:
1. Run the setup wizard
2. Start with default settings (requires ANTHROPIC_API_KEY)
3. Exit and configure manually

[Selection]

Let's set up your configuration...

? Which AI provider do you want to use?
  > Anthropic Claude
    OpenAI GPT
    Google Gemini
    Local (Ollama)

[Continue with wizard...]

Configuration saved! Starting OpenCode...
```

### Low Priority: Contextual Help

Add contextual help within the TUI:

```
# When user types "?" at start of input

Help Mode
========

Commands you can use:
- @plan - Switch to plan agent (read-only)
- @build - Switch to build agent (full access)
- @file:path - Include a file in context
- @folder:path - Include a folder in context

Tools available:
- read: Read file contents
- write: Create new files
- edit: Edit existing files
- bash: Run shell commands
- grep: Search file contents
- glob: Find files by pattern

Press Esc to exit help mode.
```

---

## Onboarding Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Time to first success | ~5 min | ~2 min |
| Documentation required | Yes | Minimal |
| Configuration errors | Common | Rare |
| User satisfaction | Medium | High |

---

## Implementation Roadmap

### Phase 1: Tutorial Command

1. Create `opencode tutorial` command
2. Implement interactive lessons
3. Add progress tracking
4. Create lesson content

### Phase 2: First-Run Detection

1. Detect first run (no config)
2. Show welcome message
3. Offer setup wizard
4. Save preferences

### Phase 3: Contextual Help

1. Add "?" help mode
2. Create command reference
3. Add tool documentation
4. Include examples

---

## Quick Start Guide Update

Update README.md quick start:

```markdown
## Quick Start

### 1. Install
```bash
pip install opencode-ai
```

### 2. Configure (Choose One)

**Option A: Use a preset (Recommended)**
```bash
cp config/presets/claude.toml ./opencode.toml
export ANTHROPIC_API_KEY=your-key
```

**Option B: Run the wizard**
```bash
opencode config wizard
```

**Option C: Set environment variable only**
```bash
export ANTHROPIC_API_KEY=your-key
```

### 3. Run
```bash
opencode
```

### 4. Learn
```bash
opencode tutorial
```
```

---

*Review completed: 2026-02-24*