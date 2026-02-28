# SkillPointer CLI Commands

This document provides a quick reference for the SkillPointer CLI commands integrated into opencode_4py.

## Overview

SkillPointer is an organizational pattern that solves the "Token Tax" problem - when you have hundreds or thousands of skills, the startup token cost becomes massive.

## Commands

### `opencode skills setup`

Set up SkillPointer architecture - migrates skills to vault and generates pointers.

```bash
# Standard setup
opencode skills setup

# With custom vault directory
opencode skills setup --vault /path/to/vault

# Dry run (show what would happen)
opencode skills setup --dry-run
```

### `opencode skills migrate`

Migrate skills to the hidden vault without generating pointers.

```bash
# Migrate all skills
opencode skills migrate

# With custom vault
opencode skills migrate --vault /path/to/vault
```

### `opencode skills generate`

Generate category pointers from existing vault.

```bash
# Generate and save pointers
opencode skills generate

# Generate without saving
opencode skills generate --no-save
```

### `opencode skills list`

List available skill categories.

```bash
# List categories
opencode skills list

# Show individual skills
opencode skills list --skills
```

### `opencode skills stats`

Show token savings statistics.

```bash
opencode skills stats
```

Example output:
```
Skill Library Statistics

Total skills: 2000

Token Analysis:
  Traditional startup:      ~80,000 tokens
  With SkillPointer:        ~255 tokens
  Savings:                   ~79,745 tokens (99.7%)
```

### `opencode skills categorize`

Show which category a skill would belong to.

```bash
opencode skills categorize react-button
# Output: react-button -> web-dev
```

### `opencode skills categories`

List all available category names.

```bash
opencode skills categories
```

### `opencode skills revert`

Revert from SkillPointer architecture.

```bash
# Revert but keep vault
opencode skills revert

# Revert and delete vault
opencode skills revert --delete-vault
```

## Architecture

The SkillPointer architecture consists of:

1. **Hidden Vault**: Skills stored at `~/.opencode-skill-libraries/`
2. **Category Pointers**: Lightweight skills in `~/.config/opencode/skills/`
3. **Dynamic Retrieval**: AI uses native tools to browse the vault

## Categories

SkillPointer supports 35+ categories including:
- ai-ml, security, web-dev, backend-dev
- devops, database, design, automation
- mobile, game-dev, business, writing
- And many more...

## Usage Example

```bash
# 1. Check current stats
opencode skills stats

# 2. Set up SkillPointer
opencode skills setup

# 3. List categories
opencode skills list

# 4. Check specific skill category
opencode skills categorize my-security-skill
```

## Configuration

SkillPointer can be configured via `opencode.yaml`:

```yaml
skills:
  pointer_mode: true
  vault_path: "~/.opencode-skill-libraries"
  threshold: 50  # Use pointers when >50 skills
  auto_categorize: true
```
