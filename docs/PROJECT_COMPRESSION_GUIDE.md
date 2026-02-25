# Project Compression Guide

This document provides instructions to create a compressed archive (zip file) of the opencode_4py project using built-in compression tools on Windows and Linux.

---

## Windows Compression

### Using PowerShell (Recommended)

PowerShell's `Compress-Archive` cmdlet is the built-in way to create zip archives on Windows.

#### Basic Usage

```powershell
# Navigate to the project directory
cd "C:\Users\RyanT\Documents\code\ClaudeCode\opencode_4py"

# Create a zip archive of the entire project
Compress-Archive -Path .\* -DestinationPath .\opencode_4py.zip

# Create a zip with a specific name and date
$date = Get-Date -Format "yyyy-MM-dd"
Compress-Archive -Path .\* -DestinationPath ".\opencode_4py_$date.zip"
```

#### Excluding Unnecessary Files

```powershell
# Create archive excluding common unnecessary directories
Compress-Archive -Path .\* -DestinationPath .\opencode_4py.zip -ExcludePattern "*.git*","*__pycache__*","*.pyc","node_modules/",".venv/","*.egg-info/","dist/","build/"
```

#### Using the -Force Flag

```powershell
# Overwrite existing archive
Compress-Archive -Path .\* -DestinationPath .\opencode_4py.zip -Force
```

#### Extract a Zip Archive

```powershell
# Extract an existing archive
Expand-Archive -Path .\opencode_4py.zip -DestinationPath .\opencode_4py

# Extract with overwrite
Expand-Archive -Path .\opencode_4py.zip -DestinationPath .\opencode_4py -Force
```

---

## Linux Compression

### Using zip Command

Most Linux distributions have `zip` pre-installed or available via package manager.

#### Basic Usage

```bash
# Navigate to the project directory
cd /path/to/opencode_4py

# Create a zip archive of the entire project
zip -r opencode_4py.zip .

# Create a zip with a specific name and date
zip -r "opencode_4py_$(date +%Y-%m-%d).zip" .
```

#### Excluding Unnecessary Files

```bash
# Create archive excluding common unnecessary directories
zip -r opencode_4py.zip . -x "*.git/*" "*__pycache__*" "*.pyc" "node_modules/*" ".venv/*" "*.egg-info/*" "dist/*" "build/*"

# Using zipexclude file
zip -r opencode_4py.zip . -x@ .zipexclude
```

#### Create a .zipexclude File

```
# .zipexclude
.git/
.gitignore
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/
.venv/
venv/
*.log
.DS_Store
node_modules/
.coverage
htmlcov/
.pytest_cache/
```

#### Using gzip Instead (Alternative)

```bash
# Create a tar.gz archive (common on Linux)
tar -czvf opencode_4py.tar.gz . --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' --exclude='.venv'

# Extract a tar.gz archive
tar -xzvf opencode_4py.tar.gz
```

---

## Python Alternative (Cross-Platform)

You can also use Python's built-in `zipfile` module to create archives from any OS.

### Create Archive

```python
import zipfile
import os
from pathlib import Path

def create_zip(source_dir: str, output_name: str):
    """Create a zip archive of a directory."""
    source_path = Path(source_dir)
    
    # Exclusions list
    exclusions = {
        '.git', '__pycache__', '.pyc', '.pyo', '.egg-info',
        'dist', 'build', '.venv', 'venv', 'node_modules',
        '.DS_Store', '.coverage', 'htmlcov', '.pytest_cache'
    }
    
    with zipfile.ZipFile(output_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in exclusions]
            
            for file in files:
                if file in exclusions or file.endswith('.pyc'):
                    continue
                
                file_path = Path(root) / file
                arcname = file_path.relative_to(source_path)
                zipf.write(file_path, arcname)

# Usage
create_zip('.', 'opencode_4py.zip')
```

### Extract Archive

```python
import zipfile

def extract_zip(zip_path: str, extract_to: str):
    """Extract a zip archive."""
    with zipfile.ZipFile(zip_path, 'r') as zipf:
        zipf.extractall(extract_to)

# Usage
extract_zip('opencode_4py.zip', './opencode_4py')
```

---

## Notes

- **7-Zip** is not installed on this system, so these alternatives are provided
- The project has a `make build` command that creates a wheel for PyPI distribution, but this is different from a full project archive
- For distribution, consider using `make build` for PyPI uploads and this compression guide for sharing complete project snapshots

---

*Last updated: 2026-02-25*
