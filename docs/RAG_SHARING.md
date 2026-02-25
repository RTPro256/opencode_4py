# RAG Sharing Guide

Share and sync RAG knowledge bases with the community.

## Quick Start

### For Repository Owner (You)

**Push your changes to GitHub:**
```bash
# Run the push script
scripts\push_to_github.bat "Add troubleshooting RAG"

# Or manually:
git add .
git commit -m "Add troubleshooting RAG"
git push -u origin main
```

### For Users (Getting Your RAG)

**Download your troubleshooting RAG:**
```bash
opencode rag get troubleshooting --from RTPro256/opencode_4py
```

### For Contributors (Sharing with You)

**Share their RAG via Pull Request:**
```bash
# Run the share script
scripts\share_rag.bat

# Or manually:
# 1. Fork https://github.com/RTPro256/opencode_4py
# 2. Add their RAG to RAG/agent_troubleshooting/
# 3. Create a Pull Request
```

## Overview

OpenCode_4py supports sharing RAG indexes through GitHub. This enables:

- **Community knowledge**: Share troubleshooting tips, error solutions, and best practices
- **Easy sync**: Download community RAGs with a single command
- **Merging**: Combine multiple RAG indexes into one

## Commands

### Download Community RAG

```bash
# Download troubleshooting RAG from RTPro256/opencode_4py
opencode rag get troubleshooting

# Download from a specific repository
opencode rag get troubleshooting --from user/opencode_4py

# Merge with existing local RAG
opencode rag get troubleshooting --merge

# Overwrite existing RAG
opencode rag get troubleshooting --force
```

### List Available RAGs

```bash
# List RAGs from RTPro256/opencode_4py
opencode rag list-remote

# List from specific repository
opencode rag list-remote --from user/opencode_4py
```

### Share Your RAG

```bash
# Share to RTPro256/opencode_4py (requires GitHub token)
opencode rag share troubleshooting

# With GitHub token
opencode rag share troubleshooting --token ghp_xxxx
```

### Merge Local RAGs

```bash
# Merge source RAG into target RAG
opencode rag merge troubleshooting my-local-fixes
```

## Repository Structure

```
RTPro256/opencode_4py
├── RAG/
│   └── agent_troubleshooting/     # Community troubleshooting RAG
│       ├── config.json
│       ├── .vector_store/
│       │   ├── data.json
│       │   └── embeddings.npy
│       └── .embedding_cache/
├── docs/
│   └── RAG_SHARING.md             # This file
└── scripts/
    ├── push_to_github.bat         # Push changes to GitHub
    └── share_rag.bat              # Share RAG via PR
```

## Simple Workflows

### Workflow 1: Update the Repository

```bash
# After making changes, push to GitHub
scripts\push_to_github.bat "Your commit message"
```

### Workflow 2: Share Your Troubleshooting Knowledge

1. Create error documents in `RAG/agent_troubleshooting/errors/`
2. Run `opencode rag create troubleshooting --source RAG/agent_troubleshooting/errors`
3. Push to GitHub: `scripts\push_to_github.bat "Add new error documents"`

### Workflow 3: Get Community Updates

```bash
# Download latest troubleshooting RAG
opencode rag get troubleshooting --merge
```

### Workflow 4: Contribute to Community

1. Fork the repository on GitHub
2. Add your error documents
3. Create a Pull Request
4. Or use: `scripts\share_rag.bat`

## RAG Document Format

Error documents should follow this format (see [BUG_DETECTION_PROCESS.md](BUG_DETECTION_PROCESS.md) for full details):

### Error Document (ERR-XXX)

```markdown
# ERR-XXX: [Error Title]

## Symptoms
What the user observes.

## Root Cause
Why this happens.

## Solution
Step-by-step fix.

## Prevention
How to avoid in the future.

## Related Errors
- ERR-YYY: Related error
```

### Bug Document (BUG-XXX)

For detected bugs including prompt quality issues:

```markdown
# BUG-XXX: [Brief Title]

## Type
- [ ] test_failure
- [ ] lint_error
- [ ] runtime_exception
- [ ] type_error
- [ ] import_error
- [ ] prompt_quality_issue

## Severity
- [ ] Critical - System unusable
- [ ] High - Major functionality broken
- [ ] Medium - Feature partially working
- [ ] Low - Minor issue, workaround available

## Symptoms
What the user/agent observes.

## Root Cause
Why this happens.

## Solution
Step-by-step fix.

## Prevention
How to avoid in the future.
```

> **Note:** Prompt quality issues include: incorrect outputs, format mismatch, ambiguity, missing context, verbosity, unclear intent. See [BUG_DETECTION_PROCESS.md](BUG_DETECTION_PROCESS.md) for details.

## Best Practices

### For RAG Creators

1. **Use consistent embedding model**: Stick with `nomic-embed-text` for compatibility
2. **Document your sources**: Include a README in your RAG folder
3. **Version your RAG**: Update `config.json` with version info
4. **Test before sharing**: Verify RAG works with `opencode rag query`

### For RAG Consumers

1. **Check compatibility**: Ensure same embedding model
2. **Merge carefully**: Use `--merge` flag to combine with existing knowledge
3. **Update regularly**: Re-run `opencode rag get` to get latest fixes

## Troubleshooting

### "RAG not found in repository"

The repository may not have the requested agent. Check available RAGs:

```bash
opencode rag list-remote --from RTPro256/opencode_4py
```

### "Different embedding models" warning

This means the RAGs use different embedding models. Merging may produce inconsistent results. Consider:

1. Recreating one RAG with the same model
2. Using the RAGs separately

### "GitHub token required"

Set your token:

```bash
# Windows (Command Prompt)
set GITHUB_TOKEN=ghp_xxxx

# Windows (PowerShell)
$env:GITHUB_TOKEN="ghp_xxxx"

# Linux/macOS
export GITHUB_TOKEN=ghp_xxxx
```

Create a token at: https://github.com/settings/tokens

### Download failed

1. Check internet connection
2. Verify repository exists and is public
3. Try again with `--force` flag

## API Reference

### `opencode rag get`

Download a community RAG index.

```
Usage: opencode rag get [OPTIONS] AGENT

Arguments:
  AGENT  Agent name to download RAG for [required]

Options:
  -f, --from TEXT  Source repository (format: owner/repo)
                   [default: RTPro256/opencode_4py]
  -o, --output TEXT  Output directory [default: ./RAG]
  -F, --force      Overwrite existing RAG
  -m, --merge      Merge with existing RAG
```

### `opencode rag share`

Share your RAG with the community.

```
Usage: opencode rag share [OPTIONS] AGENT

Arguments:
  AGENT  Agent name to share [required]

Options:
  -t, --to TEXT    Target repository [default: RTPro256/opencode_4py]
  -k, --token TEXT GitHub personal access token
  -m, --message TEXT  Commit message [default: Update RAG index]
```

### `opencode rag list-remote`

List available community RAGs.

```
Usage: opencode rag list-remote [OPTIONS]

Options:
  -f, --from TEXT  Source repository [default: RTPro256/opencode_4py]
```

### `opencode rag merge`

Merge two local RAG indexes.

```
Usage: opencode rag merge [OPTIONS] TARGET SOURCE

Arguments:
  TARGET  Target agent name [required]
  SOURCE  Source agent name to merge from [required]

Options:
  -o, --output TEXT  RAG directory [default: ./RAG]
```

## Related Documentation

- [BUG_DETECTION_PROCESS.md](BUG_DETECTION_PROCESS.md) - Bug detection and RAG documentation process
- [BEST_PRACTICE_FOR_RAG.md](BEST_PRACTICE_FOR_RAG.md) - RAG best practices
- [RAG/README.md](../RAG/README.md) - RAG system overview
- [RAG/troubleshooting/README.md](../RAG/troubleshooting/README.md) - Troubleshooting guide
