# Configuration Complexity Review

> **Review Date**: 2026-02-24
> **Scope**: User configuration experience and simplification

---

## Executive Summary

Configuration has been simplified with the addition of configuration presets. Further improvements are recommended for the configuration wizard and validation.

---

## Current State

### Configuration Methods

| Method | Description | Complexity |
|--------|-------------|------------|
| `opencode.toml` | Main configuration file | Medium |
| Environment variables | API keys and overrides | Low |
| CLI arguments | Runtime overrides | Low |
| Configuration presets | Pre-built configurations | Low |

### Environment Variables

| Variable | Description | Example |
|----------|-------------|--------|
| `OPENCODE_LOG_LEVEL` | Set log level (DEBUG, INFO, WARNING, ERROR) | `DEBUG` |
| `OPENCODE_LOG_FILE` | Set log file path | `/tmp/opencode.log` |
| `OPENCODE_LOG_MODULES` | Filter logs to specific modules | `ollama,anthropic` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-...` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `OLLAMA_HOST` | Ollama server URL | `http://localhost:11434` |

### Configuration File Structure

```toml
# opencode.toml
[provider]
default = "anthropic"

[provider.anthropic]
api_key_env = "ANTHROPIC_API_KEY"
model = "claude-sonnet-4-20250514"
max_tokens = 8192
temperature = 0.7

[tools]
bash = true
read = true
# ... more tools

[permissions]
bash_allow = ["git status", "ls"]

[mcp]
servers = []

[ui]
theme = "dark"
language = "en"
```

---

## Improvements Implemented

### Configuration Presets

Created 4 configuration presets in `config/presets/`:

| Preset | Description | Use Case |
|--------|-------------|----------|
| `claude.toml` | Anthropic Claude | Claude users |
| `openai.toml` | OpenAI GPT | GPT users |
| `local.toml` | Local Ollama | Offline/local usage |
| `multi-provider.toml` | Multi-provider | Advanced users |

### Usage

```bash
# Copy preset to project
cp config/presets/claude.toml ./opencode.toml

# Or use with profiles
opencode --profile development
```

---

## Remaining Improvements

### High Priority

#### 1. Configuration Wizard

Create `opencode config wizard` command:

```
$ opencode config wizard

Welcome to OpenCode Configuration Wizard!

? Which AI provider do you want to use?
  > Anthropic Claude
    OpenAI GPT
    Google Gemini
    Local (Ollama)

? Enter your Anthropic API key: ********

? Select default model:
  > claude-sonnet-4-20250514 (recommended)
    claude-opus-4-20250514 (most capable)
    claude-3-5-haiku-20241022 (fastest)

Configuration saved to opencode.toml
```

#### 2. Configuration Validation

Add `opencode config validate` command:

```
$ opencode config validate

Checking configuration...
  [OK] Provider: anthropic
  [OK] API key set
  [OK] Model: claude-sonnet-4-20250514
  [OK] Tools configured
  [OK] MCP servers

Configuration is valid!
```

### Medium Priority

#### 3. Improved Error Messages

Current:
```
Error: Provider anthropic not found
```

Improved:
```
Error: Provider 'anthropic' is not configured.

To fix:
1. Set ANTHROPIC_API_KEY environment variable
2. Or add to opencode.toml:
   [provider.anthropic]
   api_key_env = "ANTHROPIC_API_KEY"

Run 'opencode config wizard' for guided setup.
```

#### 4. Configuration Migration

Handle configuration changes between versions:

```
$ opencode config migrate

Migrating configuration from v1.0 to v2.0...
  [OK] Provider settings migrated
  [OK] Tool settings migrated
  [OK] New options added with defaults

Migration complete!
```

---

## Configuration Complexity Metrics

| Metric | Before | After |
|--------|--------|-------|
| Required settings | 5 | 2 (with presets) |
| Documentation pages | 3 | 1 (with wizard) |
| Setup time (new user) | ~10 min | ~2 min (with wizard) |
| Error messages | Generic | Actionable |

---

## Recommendations

### Immediate

1. ✅ Create configuration presets (DONE)
2. Add configuration wizard command
3. Add configuration validation command

### Short-term

1. Improve error messages with actionable guidance
2. Add configuration migration for version updates
3. Create interactive setup on first run

### Long-term

1. Add configuration profiles support
2. Create configuration sharing/import
3. Add configuration backup/restore

---

*Review completed: 2026-02-24*
