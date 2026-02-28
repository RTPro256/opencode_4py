# GitHub Repositories Reference

> **Navigation:**
> - **Back to:** [GITHUB_UPLOAD_PLAN.md](../plans/GITHUB_UPLOAD_PLAN.md) - GitHub upload plan
> - **Related:** [PLAN_INDEX.md](../plans/PLAN_INDEX.md) - All plans index

> **Related Documents:**
> - [README.md](../README.md) - Project overview and features
> - [TARGET_PROJECT_SYNC_PLAN.md](../plans/TARGET_PROJECT_SYNC_PLAN.md) - Target project synchronization

## Purpose

This document serves as the central reference for all GitHub repositories associated with the opencode_4py project. It provides a single source of truth for repository URLs, ownership, and configuration.

---

## Primary Repository

### opencode_4py

| Property | Value |
|----------|-------|
| **Repository Name** | `opencode_4py` |
| **Owner** | `RTPro256` |
| **Full URL** | `https://github.com/RTPro256/opencode_4py.git` |
| **SSH URL** | `git@github.com:RTPro256/opencode_4py.git` |
| **Visibility** | Public (recommended) / Private (user choice) |
| **Git LFS** | Configured |
| **Default Branch** | `main` |
| **Push Command** | `git push origin main` |
| **Content** | Full project (src, docs, plans, RAG, scripts, etc.) |

#### Future Updates

To push future updates to this repository:

```bash
cd /path/to/opencode_4py
git add .
git commit -m "Your commit message"
git push origin main
```

Or use the CLI command:
```bash
opencode github push -m "Your commit message"
``` |

#### Repository Description (suggested)

```
OpenCode Python - A privacy-first, multi-provider AI assistant with RAG capabilities, 
TUI interface, and session management. Built for developers who value data sovereignty.
```

#### Topics/Tags (suggested)

- `python`
- `ai-assistant`
- `llm`
- `rag`
- `privacy-first`
- `multi-provider`
- `terminal-ui`
- `textual`
- `session-management`
- `local-first`

---

## Target Project Repositories

These are repositories for projects in the `for_testing/` directory that may receive synchronized updates.

### ComfyUI Integration

| Property | Value |
|----------|-------|
| **Local Path** | `for_testing/as_dependency/ComfyUI_windows_portable/` |
| **Upstream URL** | `https://github.com/comfyanonymous/ComfyUI` |
| **Integration Type** | Dependency testing |
| **Sync Status** | See [TARGET_PROJECT_SYNC_PLAN.md](../plans/TARGET_PROJECT_SYNC_PLAN.md) |
| **Push Command** | N/A (external upstream) |



---

## Repository Configuration Standards

### Git LFS Tracking

All repositories should use Git LFS for the following file types:

```gitattributes




### Line Ending Configuration

```gitattributes
# Auto detect text files

## Required Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview and quick start |
| `LICENSE` | License information (MIT recommended) |
| `.gitignore` | Files to exclude from version control |
| `.gitattributes` | LFS and line ending configuration |
| `CONTRIBUTING.md` | Contribution guidelines |
| `SECURITY.md` | Security policy |

---

## Access and Authentication

### Recommended Authentication Methods

| Method | Use Case | Setup |
| **SSH Keys** | Development machines | [GitHub SSH Guide](https://docs.github.com/en/authentication/connecting-to-github-with-ssh) |
| **Personal Access Token** | CI/CD, scripts | [GitHub PAT Guide](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) |
| **GitHub CLI** | Interactive use | `gh auth login` |

### Owner Information

| Property | Value |
| **Username** | `RTPro256` |
| **Profile** | `https://github.com/RTPro256` |

---

## Repository Creation Checklist

When creating a new repository:

- [ ] Choose appropriate visibility (Public/Private)
- [ ] Add repository description
- [ ] Add relevant topics/tags
- [ ] Initialize with README (or push existing)
- [ ] Configure branch protection rules (optional)
- [ ] Set up GitHub Actions (optional)
- [ ] Configure Git LFS if needed
- [ ] Add required files (LICENSE, CONTRIBUTING.md, SECURITY.md)

---

## Future Repositories

The following repositories may be created in the future:

| Repository | Purpose | Priority | Push Command |
|------------|---------|----------|--------------|
| `opencode_4py-docs` | Dedicated documentation site | Low | `git push origin main` |
| `opencode_4py-examples` | Example projects and templates | Medium | `git push origin main` |
| `opencode_4py-templates` | Project templates | Low | `git push origin main` |

---

## Interactive Upload Workflow

### User Prompt Flow

When initiating a GitHub upload, opencode_4py should prompt the user with:

```
These are repos that I am aware of and can update:

1. opencode_4py (https://github.com/RTPro256/opencode_4py.git)
   - Primary project repository
   - Content: Full project (src, docs, plans, RAG, scripts)
   - Status: Ready to push

Is there a new repo you want me to update?
> [Enter repository name or number, or 'new' to create a new one]
```

### Response Options

| User Input | Action |
|------------|--------|
| `1` or `opencode_4py` | Execute upload to primary repository |
| `new` | Prompt for new repository details |
| `cancel` | Abort operation |

Every repository should include:

| File | Purpose |
|------|---------|
| `README.md` | Project overview and quick start |
| `LICENSE` | License information (MIT recommended) |
| `.gitignore` | Files to exclude from version control |
| `.gitattributes` | LFS and line ending configuration |
| `CONTRIBUTING.md` | Contribution guidelines |
| `SECURITY.md` | Security policy |

---

## Access and Authentication

### Recommended Authentication Methods

| Method | Use Case | Setup |
|--------|----------|-------|
| **SSH Keys** | Development machines | [GitHub SSH Guide](https://docs.github.com/en/authentication/connecting-to-github-with-ssh) |
| **Personal Access Token** | CI/CD, scripts | [GitHub PAT Guide](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) |
| **GitHub CLI** | Interactive use | `gh auth login` |

### Owner Information

| Property | Value |
|----------|-------|
| **Username** | `RTPro256` |
| **Profile** | `https://github.com/RTPro256` |

---

## Repository Creation Checklist

When creating a new repository:

- [ ] Choose appropriate visibility (Public/Private)
- [ ] Add repository description
- [ ] Add relevant topics/tags
- [ ] Initialize with README (or push existing)
- [ ] Configure branch protection rules (optional)
- [ ] Set up GitHub Actions (optional)
- [ ] Configure Git LFS if needed
- [ ] Add required files (LICENSE, CONTRIBUTING.md, SECURITY.md)

---

## Future Repositories

The following repositories may be created in the future:

| Repository | Purpose | Priority | Push Command |
|------------|---------|----------|--------------|
| `opencode_4py-docs` | Dedicated documentation site | Low | `git push origin main` |
| `opencode_4py-examples` | Example projects and templates | Medium | `git push origin main` |
| `opencode_4py-templates` | Project templates | Low | `git push origin main` |

---

## Interactive Upload Workflow

### User Prompt Flow

When initiating a GitHub upload, opencode_4py should prompt the user with:

```
These are repos that I am aware of and can update:

1. opencode_4py (https://github.com/RTPro256/opencode_4py.git)
   - Primary project repository
   - Content: Full project (src, docs, plans, RAG, scripts)
   - Status: Ready to push


   - Content: Python package only (pip-installable)
   - Status: Active

Is there a new repo you want me to update?
> [Enter repository name or number, or 'new' to create a new one]
```

### Response Options

| User Input | Action |
|------------|--------|
| `1` or `opencode_4py` | Execute upload to primary repository |
| `new` | Prompt for new repository details |
| `cancel` | Abort operation |

### New Repository Creation Flow

If user selects `new`:

```
Creating a new repository...

Repository name: [user input]
Description: [user input]
Visibility (public/private): [user input]
Git LFS enabled (y/n): [default: y]

Confirm creation? (y/n): [user input]
```

---

## Failure Recovery

### Common Failure Scenarios

| Error | Cause | Recovery Steps |
|-------|-------|----------------|
| `fatal: repository not found` | Remote doesn't exist | Create repository on GitHub first |
| `fatal: HTTP 413` | Request too large | Check for large files, configure Git LFS |
| `LFS: object not found` | LFS not configured | Run `git lfs install` and re-commit |
| `fatal: refused to push` | Branch protection | Check GitHub branch protection rules |
| `error: failed to push some refs` | Remote has changes | Pull first: `git pull --rebase origin main` |
| `LF will be replaced by CRLF` | Line ending mismatch | Configure `.gitattributes` properly |

### Recovery Commands

```bash
# Reset local repository (nuclear option)
rm -rf .git
git init
git lfs install
git add .
git commit -m "Fresh start"

# Fix LFS issues
git lfs migrate import --include="*.dll,*.pyd,*.pkl" --everything

# Force push (use with extreme caution)
git push -f origin main

# Reconfigure remote
git remote remove origin
git remote add origin https://github.com/RTPro256/REPO_NAME.git
```

### Failure Response Template

When a failure occurs, opencode_4py should respond:

```
Upload failed with error: [ERROR_MESSAGE]

Recommended recovery steps:
1. [Step 1 specific to error]
2. [Step 2 specific to error]
3. [Step 3 specific to error]

Would you like me to attempt automatic recovery? (y/n)
```

---

## Change Log

| Date | Change |
|------|--------|

| 2026-02-27 | Added quick sync one-liner command |
| 2026-02-25 | Added push command instructions to all repository sections |

| 2026-02-25 | Added interactive upload workflow section |
| 2026-02-25 | Added failure recovery section |
| 2026-02-25 | Initial creation - reference document for GITHUB_UPLOAD_PLAN.md |

---

*Created: 2026-02-25*
*Author: OpenCode AI Assistant*
