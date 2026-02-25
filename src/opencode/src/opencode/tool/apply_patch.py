"""
Apply patch tool for applying structured patches to files.

This tool implements a custom patch format that supports:
- Adding new files
- Deleting existing files
- Updating files with line-based changes
- Moving/renaming files during updates
"""

import os
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field


@dataclass
class UpdateFileChunk:
    """Represents a chunk of changes in an update operation."""
    old_lines: list[str] = field(default_factory=list)
    new_lines: list[str] = field(default_factory=list)
    change_context: Optional[str] = None
    is_end_of_file: bool = False


@dataclass
class Hunk:
    """Base class for patch hunks."""
    pass


@dataclass
class AddHunk(Hunk):
    """Hunk for adding a new file."""
    type: str = "add"
    path: str = ""
    contents: str = ""


@dataclass
class DeleteHunk(Hunk):
    """Hunk for deleting a file."""
    type: str = "delete"
    path: str = ""


@dataclass
class UpdateHunk(Hunk):
    """Hunk for updating a file."""
    type: str = "update"
    path: str = ""
    move_path: Optional[str] = None
    chunks: list[UpdateFileChunk] = field(default_factory=list)


def parse_patch_header(lines: list[str], start_idx: int) -> Optional[dict[str, Any]]:
    """Parse a patch header line to extract file path and optional move path."""
    if start_idx >= len(lines):
        return None
    
    line = lines[start_idx]
    
    if line.startswith("*** Add File:"):
        file_path = line.split(":", 1)[1].strip() if ":" in line else ""
        return {"file_path": file_path, "type": "add", "next_idx": start_idx + 1}
    
    if line.startswith("*** Delete File:"):
        file_path = line.split(":", 1)[1].strip() if ":" in line else ""
        return {"file_path": file_path, "type": "delete", "next_idx": start_idx + 1}
    
    if line.startswith("*** Update File:"):
        file_path = line.split(":", 1)[1].strip() if ":" in line else ""
        move_path = None
        next_idx = start_idx + 1
        
        # Check for move directive
        if next_idx < len(lines) and lines[next_idx].startswith("*** Move to:"):
            move_path = lines[next_idx].split(":", 1)[1].strip() if ":" in lines[next_idx] else ""
            next_idx += 1
        
        return {"file_path": file_path, "type": "update", "move_path": move_path, "next_idx": next_idx}
    
    return None


def parse_update_file_chunks(lines: list[str], start_idx: int) -> tuple[list[UpdateFileChunk], int]:
    """Parse chunks for an update operation."""
    chunks: list[UpdateFileChunk] = []
    i = start_idx
    
    while i < len(lines) and not lines[i].startswith("***"):
        if lines[i].startswith("@@"):
            # Parse context line
            context_line = lines[i][2:].strip()
            i += 1
            
            old_lines: list[str] = []
            new_lines: list[str] = []
            is_end_of_file = False
            
            # Parse change lines
            while i < len(lines) and not lines[i].startswith("@@") and not lines[i].startswith("***"):
                change_line = lines[i]
                
                if change_line == "*** End of File":
                    is_end_of_file = True
                    i += 1
                    break
                
                if change_line.startswith(" "):
                    # Keep line - appears in both old and new
                    content = change_line[1:]
                    old_lines.append(content)
                    new_lines.append(content)
                elif change_line.startswith("-"):
                    # Remove line - only in old
                    old_lines.append(change_line[1:])
                elif change_line.startswith("+"):
                    # Add line - only in new
                    new_lines.append(change_line[1:])
                
                i += 1
            
            chunks.append(UpdateFileChunk(
                old_lines=old_lines,
                new_lines=new_lines,
                change_context=context_line or None,
                is_end_of_file=is_end_of_file,
            ))
        else:
            i += 1
    
    return chunks, i


def parse_add_file_content(lines: list[str], start_idx: int) -> tuple[str, int]:
    """Parse content for an add operation."""
    content_lines: list[str] = []
    i = start_idx
    
    while i < len(lines) and not lines[i].startswith("***"):
        if lines[i].startswith("+"):
            content_lines.append(lines[i][1:])
        i += 1
    
    return "\n".join(content_lines), i


def strip_heredoc(input_text: str) -> str:
    """Strip heredoc wrapper if present."""
    import re
    heredoc_match = re.match(r"^(?:cat\s+)?<<['\"]?(\w+)['\"]?\s*\n([\s\S]*?)\n\1\s*$", input_text)
    if heredoc_match:
        return heredoc_match.group(2)
    return input_text


def parse_patch(patch_text: str) -> list[Hunk]:
    """Parse a patch text into a list of hunks."""
    cleaned = strip_heredoc(patch_text.strip())
    lines = cleaned.split("\n")
    hunks: list[Hunk] = []
    
    # Look for Begin/End patch markers
    begin_marker = "*** Begin Patch"
    end_marker = "*** End Patch"
    
    begin_idx = -1
    end_idx = -1
    
    for i, line in enumerate(lines):
        if line.strip() == begin_marker:
            begin_idx = i
        elif line.strip() == end_marker:
            end_idx = i
            break
    
    if begin_idx == -1 or end_idx == -1 or begin_idx >= end_idx:
        raise ValueError("Invalid patch format: missing Begin/End markers")
    
    # Parse content between markers
    i = begin_idx + 1
    
    while i < end_idx:
        header = parse_patch_header(lines, i)
        if not header:
            i += 1
            continue
        
        if header["type"] == "add":
            content, next_idx = parse_add_file_content(lines, header["next_idx"])
            hunks.append(AddHunk(
                type="add",
                path=header["file_path"],
                contents=content,
            ))
            i = next_idx
        elif header["type"] == "delete":
            hunks.append(DeleteHunk(
                type="delete",
                path=header["file_path"],
            ))
            i = header["next_idx"]
        elif header["type"] == "update":
            chunks, next_idx = parse_update_file_chunks(lines, header["next_idx"])
            hunks.append(UpdateHunk(
                type="update",
                path=header["file_path"],
                move_path=header.get("move_path"),
                chunks=chunks,
            ))
            i = next_idx
        else:
            i += 1
    
    return hunks


def seek_sequence(haystack: list[str], needle: list[str], start_idx: int = 0, is_end_of_file: bool = False) -> int:
    """Find the starting index of a sequence in a list."""
    if not needle:
        return start_idx
    
    for i in range(start_idx, len(haystack) - len(needle) + 1):
        match = True
        for j, n in enumerate(needle):
            if i + j >= len(haystack) or haystack[i + j] != n:
                match = False
                break
        if match:
            return i
    
    # If end of file, try searching from the end
    if is_end_of_file and len(needle) <= len(haystack):
        for i in range(len(haystack) - len(needle), max(start_idx - 1, -1), -1):
            match = True
            for j, n in enumerate(needle):
                if i + j >= len(haystack) or haystack[i + j] != n:
                    match = False
                    break
            if match:
                return i
    
    return -1


def compute_replacements(
    original_lines: list[str],
    file_path: str,
    chunks: list[UpdateFileChunk],
) -> list[tuple[int, int, list[str]]]:
    """Compute line replacements for update chunks."""
    replacements: list[tuple[int, int, list[str]]] = []
    line_index = 0
    
    for chunk in chunks:
        # Handle context-based seeking
        if chunk.change_context:
            context_idx = seek_sequence(original_lines, [chunk.change_context], line_index)
            if context_idx == -1:
                raise ValueError(f"Failed to find context '{chunk.change_context}' in {file_path}")
            line_index = context_idx + 1
        
        # Handle pure addition (no old lines)
        if not chunk.old_lines:
            insertion_idx = len(original_lines)
            replacements.append((insertion_idx, 0, chunk.new_lines))
            continue
        
        # Try to match old lines in the file
        pattern = chunk.old_lines.copy()
        new_slice = chunk.new_lines.copy()
        found = seek_sequence(original_lines, pattern, line_index, chunk.is_end_of_file)
        
        # Retry without trailing empty line if not found
        if found == -1 and pattern and pattern[-1] == "":
            pattern = pattern[:-1]
            if new_slice and new_slice[-1] == "":
                new_slice = new_slice[:-1]
            found = seek_sequence(original_lines, pattern, line_index, chunk.is_end_of_file)
        
        if found != -1:
            replacements.append((found, len(pattern), new_slice))
            line_index = found + len(pattern)
        else:
            raise ValueError(f"Failed to find expected lines in {file_path}:\n" + "\n".join(chunk.old_lines))
    
    # Sort replacements by index
    replacements.sort(key=lambda x: x[0])
    
    return replacements


def apply_replacements(original_lines: list[str], replacements: list[tuple[int, int, list[str]]]) -> list[str]:
    """Apply computed replacements to generate new lines."""
    if not replacements:
        return original_lines.copy()
    
    result: list[str] = []
    last_idx = 0
    
    for start_idx, remove_count, new_lines in replacements:
        # Add lines before this replacement
        result.extend(original_lines[last_idx:start_idx])
        # Add replacement lines
        result.extend(new_lines)
        # Skip removed lines
        last_idx = start_idx + remove_count
    
    # Add remaining lines
    result.extend(original_lines[last_idx:])
    
    return result


def derive_new_contents_from_chunks(file_path: str, chunks: list[UpdateFileChunk]) -> tuple[str, str]:
    """Derive new file contents from update chunks."""
    # Read original file content
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            original_content = f.read()
    except Exception as e:
        raise ValueError(f"Failed to read file {file_path}: {e}")
    
    original_lines = original_content.split("\n")
    
    # Drop trailing empty element for consistent line counting
    if original_lines and original_lines[-1] == "":
        original_lines.pop()
    
    replacements = compute_replacements(original_lines, file_path, chunks)
    new_lines = apply_replacements(original_lines, replacements)
    
    # Ensure trailing newline
    if not new_lines or new_lines[-1] != "":
        new_lines.append("")
    
    new_content = "\n".join(new_lines)
    
    # Generate unified diff
    unified_diff = generate_unified_diff(original_content, new_content, file_path)
    
    return unified_diff, new_content


def generate_unified_diff(old_content: str, new_content: str, file_path: str) -> str:
    """Generate a unified diff between old and new content."""
    import difflib
    
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=file_path,
        tofile=file_path,
    )
    
    return "".join(diff)


def trim_diff(diff: str) -> str:
    """Trim diff header lines for cleaner output."""
    lines = diff.split("\n")
    # Skip the first two header lines if present
    if len(lines) > 2 and lines[0].startswith("---") and lines[1].startswith("+++"):
        return "\n".join(lines[2:])
    return diff


# Tool implementation
from opencode.tool.base import Tool, ToolResult


class ApplyPatchTool(Tool):
    """Tool for applying structured patches to files."""
    
    @property
    def name(self) -> str:
        return "apply_patch"
    
    @property
    def description(self) -> str:
        return """Apply a structured patch to files.

This tool applies a custom patch format that supports:
- Adding new files
- Deleting existing files  
- Updating files with line-based changes
- Moving/renaming files during updates

The patch format uses markers:
- *** Begin Patch / *** End Patch - Wrap the patch content
- *** Add File: path - Add a new file
- *** Delete File: path - Delete a file
- *** Update File: path - Update an existing file
- *** Move to: newpath - Move the file during update
- @@ context - Start a change chunk with context
- Lines starting with ' ' (keep), '-' (remove), '+' (add)
- *** End of File - Mark end of file content

Example patch:
*** Begin Patch
*** Add File: src/hello.py
+def hello():
+    print("Hello, World!")
*** Update File: src/main.py
@@ def main():
 def main():
-    pass
+    hello()
*** End Patch"""
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "patchText": {
                    "type": "string",
                    "description": "The full patch text that describes all changes to be made",
                }
            },
            "required": ["patchText"],
        }
    
    async def execute(self, **params: Any) -> ToolResult:
        """Execute the patch application."""
        patch_text = params.get("patchText", "")
        
        if not patch_text:
            return ToolResult.err("patchText is required")
        
        # Parse the patch to get hunks
        try:
            hunks = parse_patch(patch_text)
        except Exception as e:
            normalized = patch_text.replace("\r\n", "\n").replace("\r", "\n").strip()
            if normalized == "*** Begin Patch\n*** End Patch":
                return ToolResult.err("patch rejected: empty patch")
            return ToolResult.err(f"apply_patch verification failed: {e}")
        
        if not hunks:
            return ToolResult.err("apply_patch verification failed: no hunks found")
        
        # Get working directory
        workdir = Path.cwd()
        
        # Track file changes
        file_changes: list[dict[str, Any]] = []
        total_diff = ""
        
        for hunk in hunks:
            if isinstance(hunk, AddHunk):
                file_path = workdir / hunk.path
                # Add new file
                new_content = hunk.contents
                if new_content and not new_content.endswith("\n"):
                    new_content += "\n"
                
                diff = trim_diff(generate_unified_diff("", new_content, str(file_path)))
                
                # Count additions
                additions = len(new_content.split("\n"))
                if new_content.endswith("\n"):
                    additions -= 1
                
                file_changes.append({
                    "file_path": str(file_path),
                    "relative_path": hunk.path,
                    "type": "add",
                    "old_content": "",
                    "new_content": new_content,
                    "diff": diff,
                    "additions": additions,
                    "deletions": 0,
                })
                total_diff += diff + "\n"
                
            elif isinstance(hunk, DeleteHunk):
                file_path = workdir / hunk.path
                # Delete file
                if not file_path.exists():
                    return ToolResult.err(f"File to delete not found: {file_path}")
                
                try:
                    old_content = file_path.read_text(encoding="utf-8")
                except Exception as e:
                    return ToolResult.err(str(e))
                
                diff = trim_diff(generate_unified_diff(old_content, "", str(file_path)))
                deletions = len(old_content.split("\n"))
                if old_content.endswith("\n"):
                    deletions -= 1
                
                file_changes.append({
                    "file_path": str(file_path),
                    "relative_path": hunk.path,
                    "type": "delete",
                    "old_content": old_content,
                    "new_content": "",
                    "diff": diff,
                    "additions": 0,
                    "deletions": deletions,
                })
                total_diff += diff + "\n"
                
            elif isinstance(hunk, UpdateHunk):
                file_path = workdir / hunk.path
                # Update existing file
                if not file_path.exists():
                    return ToolResult.err(f"Failed to read file to update: {file_path}")
                
                try:
                    unified_diff, new_content = derive_new_contents_from_chunks(str(file_path), hunk.chunks)
                except Exception as e:
                    return ToolResult.err(str(e))
                
                diff = trim_diff(unified_diff)
                
                old_content = file_path.read_text(encoding="utf-8")
                
                # Count changes
                old_lines = old_content.split("\n")
                new_lines = new_content.split("\n")
                additions = max(0, len(new_lines) - len(old_lines))
                deletions = max(0, len(old_lines) - len(new_lines))
                
                move_path = None
                if hunk.move_path:
                    move_path = str(workdir / hunk.move_path)
                
                file_changes.append({
                    "file_path": str(file_path),
                    "relative_path": hunk.path,
                    "type": "move" if hunk.move_path else "update",
                    "old_content": old_content,
                    "new_content": new_content,
                    "diff": diff,
                    "additions": additions,
                    "deletions": deletions,
                    "move_path": move_path,
                })
                total_diff += diff + "\n"
        
        # Apply the changes
        for change in file_changes:
            file_path = Path(change["file_path"])
            
            if change["type"] == "add":
                # Create parent directories
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(change["new_content"], encoding="utf-8")
                
            elif change["type"] == "delete":
                file_path.unlink()
                
            elif change["type"] == "update":
                file_path.write_text(change["new_content"], encoding="utf-8")
                
            elif change["type"] == "move":
                move_path = Path(change["move_path"])
                move_path.parent.mkdir(parents=True, exist_ok=True)
                move_path.write_text(change["new_content"], encoding="utf-8")
                file_path.unlink()
        
        # Generate output summary
        summary_lines = []
        for change in file_changes:
            if change["type"] == "add":
                summary_lines.append(f"A {change['relative_path']}")
            elif change["type"] == "delete":
                summary_lines.append(f"D {change['relative_path']}")
            elif change["type"] == "move":
                summary_lines.append(f"R {change['relative_path']} -> {Path(change['move_path']).relative_to(workdir)}")
            else:
                summary_lines.append(f"M {change['relative_path']}")
        
        output = f"Success. Updated the following files:\n" + "\n".join(summary_lines)
        
        return ToolResult.ok(
            output=output,
            metadata={
                "diff": total_diff,
                "files": file_changes,
            },
        )
