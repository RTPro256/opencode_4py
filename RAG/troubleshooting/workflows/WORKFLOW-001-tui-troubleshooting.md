# WORKFLOW-001: TUI Troubleshooting Workflow

## Metadata
- **Workflow ID**: WORKFLOW-001
- **Category**: Diagnosis Workflow
- **Applies To**: TUI application issues

## Overview

This workflow guides the debugging agent through systematic diagnosis of TUI issues.

## Workflow Steps

```mermaid
flowchart TD
    A[User Reports TUI Issue] --> B{Issue Type?}
    B -->|Stall/Hang| C[TUI Stall Diagnosis]
    B -->|Error Message| D[Error Message Analysis]
    B -->|UI Not Updating| E[UI Update Diagnosis]
    
    C --> F[Enable Debug Logging]
    F --> G[Reproduce Issue]
    G --> H[Analyze Log File]
    H --> I{Found Error?}
    I -->|Yes| J[Apply Fix from ERR-XXX]
    I -->|No| K[Check Provider Connection]
    
    D --> L[Search Error in RAG]
    L --> M{Found Match?}
    M -->|Yes| J
    M -->|No| N[Create New Error Document]
    
    E --> O[Check Reactive Properties]
    O --> P[Verify watch_ Methods]
    P --> Q{Issue Found?}
    Q -->|Yes| J
    Q -->|No| R[Check Render Method]
    
    J --> S[Verify Fix]
    S --> T{Issue Resolved?}
    T -->|Yes| U[Document in RAG]
    T -->|No| A
    
    K --> V{Provider OK?}
    V -->|Yes| H
    V -->|No| W[Fix Provider Issue]
    W --> S
    
    N --> X[Investigate Manually]
    X --> J
```

## Step Details

### Step 1: Identify Issue Type

Ask the user to describe the issue:
- **Stall/Hang**: Application freezes, shows "Thinking..." indefinitely
- **Error Message**: Application shows an error
- **UI Not Updating**: Application runs but UI doesn't reflect changes

### Step 2: Enable Debug Logging

```batch
set OPENCODE_LOG_LEVEL=DEBUG
set OPENCODE_LOG_FILE=%~dp0python_embeded\Lib\site-packages\opencode\docs\opencode_debug.log
```

### Step 3: Search Troubleshooting RAG

```bash
opencode rag query --agent troubleshooting "TUI stalls at Thinking"
```

### Step 4: Apply Fix

If a matching error is found, apply the fix from the error document.

### Step 5: Verify Fix

1. Run the application
2. Reproduce the original issue
3. Confirm the issue is resolved

### Step 6: Document New Errors

If the issue was not in the RAG:
1. Create new error document in `RAG/troubleshooting/errors/`
2. Update the RAG index

## Related Patterns
- PATTERN-001: TUI Stall Diagnosis
- PATTERN-002: Provider Connection Diagnosis

## Related Errors
- ERR-010: Async Generator Await Error
- ERR-014: Reactive Property Watch Missing
- ERR-015: Installed vs Source Mismatch
