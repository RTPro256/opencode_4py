#!/usr/bin/env python3
"""
Code Analysis Script for OpenCode

Analyzes source code for:
- Large files (>500 lines or >20K chars)
- Long functions (>50 lines)
- Module dependencies
- Code quality metrics

Usage:
    python scripts/analyze_code.py [--full]
"""

import ast
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from collections import defaultdict


@dataclass
class FileInfo:
    """Information about a source file."""
    path: Path
    lines: int
    chars: int
    functions: int
    classes: int
    long_functions: list[tuple[str, int]]  # (name, lines)


@dataclass
class FunctionInfo:
    """Information about a function."""
    name: str
    file: Path
    start_line: int
    end_line: int
    lines: int
    is_method: bool


def find_python_files(root: Path) -> list[Path]:
    """Find all Python files in the project."""
    exclude_dirs = {'.venv', 'venv', '__pycache__', '.git', 'node_modules', 'build', 'dist', 'merge_projects', 'for_testing'}
    files = []
    for p in root.rglob("*.py"):
        # Skip excluded directories
        if any(excluded in p.parts for excluded in exclude_dirs):
            continue
        files.append(p)
    return sorted(files)


def analyze_file(file_path: Path) -> FileInfo:
    """Analyze a single Python file."""
    content = file_path.read_text(encoding='utf-8', errors='replace')
    lines = content.count('\n') + 1
    chars = len(content)
    
    functions = []
    classes = 0
    long_functions = []
    
    try:
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.end_lineno is not None:
                    func_lines = node.end_lineno - node.lineno + 1
                    functions.append((node.name, func_lines))
                    if func_lines > 50:
                        long_functions.append((node.name, func_lines))
            elif isinstance(node, ast.ClassDef):
                classes += 1
    except SyntaxError:
        pass  # Skip files with syntax errors
    
    return FileInfo(
        path=file_path,
        lines=lines,
        chars=chars,
        functions=len(functions),
        classes=classes,
        long_functions=long_functions
    )


def analyze_dependencies(root: Path) -> dict[str, set[str]]:
    """Analyze module dependencies."""
    deps = defaultdict(set)
    src_root = root / "src" / "opencode" / "src" / "opencode"
    
    if not src_root.exists():
        return dict(deps)
    
    for py_file in src_root.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        
        try:
            content = py_file.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            module_name = str(py_file.relative_to(src_root).with_suffix('')).replace('/', '.')
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith('opencode'):
                            deps[module_name].add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith('opencode'):
                        deps[module_name].add(node.module)
        except (SyntaxError, Exception):
            pass
    
    return dict(deps)


def find_circular_dependencies(deps: dict[str, set[str]]) -> list[list[str]]:
    """Find circular dependencies in modules."""
    cycles = []
    visited = set()
    
    def dfs(node: str, path: list[str], visited_set: set[str]):
        if node in visited_set:
            # Found a cycle
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            return cycle
        
        if node in visited:
            return None
        
        visited_set.add(node)
        path.append(node)
        
        for dep in deps.get(node, set()):
            cycle = dfs(dep, path, visited_set.copy())
            if cycle:
                return cycle
        
        return None
    
    for module in deps:
        if module not in visited:
            cycle = dfs(module, [], set())
            if cycle:
                # Normalize cycle to avoid duplicates
                min_idx = cycle.index(min(cycle[:-1]))
                normalized = cycle[min_idx:-1] + cycle[:min_idx] + [cycle[min_idx]]
                if normalized not in cycles:
                    cycles.append(normalized)
                visited.update(normalized)
    
    return cycles


def generate_report(root: Path, files: list[FileInfo], deps: dict[str, set[str]]) -> str:
    """Generate analysis report."""
    lines = [
        "# Code Analysis Report",
        "",
        f"**Generated**: {__import__('datetime').datetime.now().isoformat()}",
        f"**Root**: {root}",
        "",
    ]
    
    # Large files analysis
    large_files = [f for f in files if f.lines > 500 or f.chars > 20000]
    large_files.sort(key=lambda f: f.chars, reverse=True)
    
    lines.append("## Large Files (>500 lines or >20K chars)")
    lines.append("")
    
    if large_files:
        lines.append("| File | Lines | Chars | Functions | Classes | Long Functions |")
        lines.append("|------|-------|-------|-----------|---------|----------------|")
        for f in large_files:
            rel_path = f.path.relative_to(root) if f.path.is_relative_to(root) else f.path
            long_funcs = len(f.long_functions)
            lines.append(f"| `{rel_path}` | {f.lines} | {f.chars:,} | {f.functions} | {f.classes} | {long_funcs} |")
        lines.append("")
    else:
        lines.append("No large files found.")
        lines.append("")
    
    # Long functions
    all_long_funcs = []
    for f in files:
        for name, func_lines in f.long_functions:
            all_long_funcs.append((f.path, name, func_lines))
    all_long_funcs.sort(key=lambda x: x[2], reverse=True)
    
    lines.append("## Long Functions (>50 lines)")
    lines.append("")
    
    if all_long_funcs:
        lines.append("| File | Function | Lines |")
        lines.append("|------|----------|-------|")
        for path, name, func_lines in all_long_funcs[:20]:  # Top 20
            rel_path = path.relative_to(root) if path.is_relative_to(root) else path
            lines.append(f"| `{rel_path}` | `{name}()` | {func_lines} |")
        if len(all_long_funcs) > 20:
            lines.append(f"| ... | ... | ({len(all_long_funcs) - 20} more) |")
        lines.append("")
    else:
        lines.append("No long functions found.")
        lines.append("")
    
    # Circular dependencies
    cycles = find_circular_dependencies(deps)
    
    lines.append("## Circular Dependencies")
    lines.append("")
    
    if cycles:
        for i, cycle in enumerate(cycles, 1):
            lines.append(f"### Cycle {i}")
            lines.append("")
            lines.append(" -> ".join(cycle))
            lines.append("")
    else:
        lines.append("No circular dependencies detected.")
        lines.append("")
    
    # Summary
    total_lines = sum(f.lines for f in files)
    total_chars = sum(f.chars for f in files)
    total_funcs = sum(f.functions for f in files)
    total_classes = sum(f.classes for f in files)
    
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total files**: {len(files)}")
    lines.append(f"- **Total lines**: {total_lines:,}")
    lines.append(f"- **Total characters**: {total_chars:,}")
    lines.append(f"- **Total functions**: {total_funcs}")
    lines.append(f"- **Total classes**: {total_classes}")
    lines.append(f"- **Large files**: {len(large_files)}")
    lines.append(f"- **Long functions**: {len(all_long_funcs)}")
    lines.append(f"- **Circular dependencies**: {len(cycles)}")
    
    return '\n'.join(lines)


def main():
    """Main entry point."""
    root = Path(__file__).parent.parent
    
    print("Finding Python files...")
    py_files = find_python_files(root)
    
    print(f"Analyzing {len(py_files)} files...")
    file_infos = []
    for i, py_file in enumerate(py_files):
        if (i + 1) % 50 == 0:
            print(f"  Progress: {i + 1}/{len(py_files)}")
        file_infos.append(analyze_file(py_file))
    
    print("Analyzing dependencies...")
    deps = analyze_dependencies(root)
    
    print("Generating report...")
    report = generate_report(root, file_infos, deps)
    
    # Write report
    report_path = root / "docs" / "CODE_ANALYSIS_REPORT.md"
    report_path.write_text(report, encoding='utf-8')
    print(f"Report written to: {report_path}")
    
    # Print summary only
    summary_start = report.find("## Summary")
    if summary_start > 0:
        print("\n" + report[summary_start:])


if __name__ == "__main__":
    main()
