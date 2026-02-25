#!/usr/bin/env python3
"""
Link Checker Script for OpenCode Documentation

Scans all markdown files for broken internal links and verifies
code file references exist.

Usage:
    python scripts/check_links.py [--fix]
"""

import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class BrokenLink:
    """Represents a broken link found in a document."""
    file: Path
    line: int
    link: str
    reason: str


def find_markdown_files(root: Path) -> list[Path]:
    """Find all markdown files in the project."""
    return list(root.rglob("*.md"))


def extract_links(content: str) -> list[tuple[int, str]]:
    """Extract all markdown links from content with line numbers.
    
    Returns list of (line_number, link_target) tuples.
    """
    # Match [text](link) pattern
    pattern = r'\[([^\]]*)\]\(([^)]+)\)'
    links = []
    
    for i, line in enumerate(content.split('\n'), 1):
        for match in re.finditer(pattern, line):
            link = match.group(2)
            # Skip external links and anchors
            if link.startswith(('http://', 'https://', '#', 'mailto:')):
                continue
            links.append((i, link))
    
    return links


def check_link(root: Path, source_file: Path, link: str) -> Optional[str]:
    """Check if a link target exists.
    
    Returns None if valid, or error reason if broken.
    """
    # Handle relative paths
    source_dir = source_file.parent
    
    # Remove anchor if present
    link_path = link.split('#')[0]
    
    if not link_path:
        # Pure anchor link, assume valid
        return None
    
    # Resolve the target path
    target = (source_dir / link_path).resolve()
    
    if not target.exists():
        return f"Target does not exist: {target.relative_to(root) if target.is_relative_to(root) else target}"
    
    return None


def check_all_links(root: Path) -> list[BrokenLink]:
    """Check all markdown files for broken links."""
    broken = []
    md_files = find_markdown_files(root)
    
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8')
        except Exception as e:
            broken.append(BrokenLink(
                file=md_file,
                line=0,
                link="N/A",
                reason=f"Could not read file: {e}"
            ))
            continue
        
        links = extract_links(content)
        
        for line_num, link in links:
            reason = check_link(root, md_file, link)
            if reason:
                broken.append(BrokenLink(
                    file=md_file,
                    line=line_num,
                    link=link,
                    reason=reason
                ))
    
    return broken


def check_code_references(root: Path) -> list[BrokenLink]:
    """Check if code file references in documentation exist."""
    broken = []
    md_files = find_markdown_files(root)
    
    # Pattern for code file references like `src/opencode/...`
    code_pattern = r'`([a-zA-Z0-9_/.-]+\.(py|toml|yaml|json|sh|bat))`'
    
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8')
        except Exception:
            continue
        
        for i, line in enumerate(content.split('\n'), 1):
            for match in re.finditer(code_pattern, line):
                ref = match.group(1)
                # Check if it's a relative path from root
                target = root / ref
                if not target.exists():
                    # Try relative to docs directory
                    if 'docs' in str(md_file):
                        target = md_file.parent.parent / ref
                    if not target.exists():
                        broken.append(BrokenLink(
                            file=md_file,
                            line=i,
                            link=ref,
                            reason=f"Code file does not exist: {ref}"
                        ))
    
    return broken


def generate_report(root: Path, broken_links: list[BrokenLink], broken_refs: list[BrokenLink]) -> str:
    """Generate a report of broken links."""
    lines = [
        "# Link Check Report",
        "",
        f"**Generated**: {__import__('datetime').datetime.now().isoformat()}",
        f"**Root**: {root}",
        "",
    ]
    
    if not broken_links and not broken_refs:
        lines.append("## [OK] All Links Valid")
        lines.append("")
        lines.append("No broken links or missing code references found.")
        return '\n'.join(lines)
    
    if broken_links:
        lines.append("## [X] Broken Markdown Links")
        lines.append("")
        lines.append("| File | Line | Link | Reason |")
        lines.append("|------|------|------|--------|")
        for bl in sorted(broken_links, key=lambda x: (str(x.file), x.line)):
            rel_file = bl.file.relative_to(root) if bl.file.is_relative_to(root) else bl.file
            lines.append(f"| {rel_file} | {bl.line} | `{bl.link}` | {bl.reason} |")
        lines.append("")
    
    if broken_refs:
        lines.append("## [X] Missing Code References")
        lines.append("")
        lines.append("| File | Line | Reference | Reason |")
        lines.append("|------|------|-----------|--------|")
        for bl in sorted(broken_refs, key=lambda x: (str(x.file), x.line)):
            rel_file = bl.file.relative_to(root) if bl.file.is_relative_to(root) else bl.file
            lines.append(f"| {rel_file} | {bl.line} | `{bl.link}` | {bl.reason} |")
        lines.append("")
    
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Broken markdown links: {len(broken_links)}")
    lines.append(f"- Missing code references: {len(broken_refs)}")
    
    return '\n'.join(lines)


def main():
    """Main entry point."""
    root = Path(__file__).parent.parent
    
    print("Checking markdown links...")
    broken_links = check_all_links(root)
    
    print("Checking code references...")
    broken_refs = check_code_references(root)
    
    report = generate_report(root, broken_links, broken_refs)
    print(report)
    
    # Write report to file
    report_path = root / "docs" / "LINK_CHECK_REPORT.md"
    report_path.write_text(report, encoding='utf-8')
    print(f"\nReport written to: {report_path}")
    
    # Exit with error code if broken links found
    if broken_links or broken_refs:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
