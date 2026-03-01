"""
Zero-conflict hash ID generation for tasks.

Based on beads (https://github.com/steveyegge/beads)

Hash-based IDs prevent merge collisions in multi-agent/multi-branch workflows.
"""

import hashlib
import random
import string
from typing import Optional


def generate_task_id(prefix: str = "bd", parent_id: Optional[str] = None) -> str:
    """
    Generate a zero-conflict hash-based task ID.
    
    Args:
        prefix: Prefix for the ID (default: "bd")
        parent_id: Parent task ID for hierarchical tasks (e.g., "bd-a3f8.1")
    
    Returns:
        A unique hash-based task ID (e.g., "bd-a1b2" or "bd-a3f8.1.1")
    
    Examples:
        >>> generate_task_id()
        'bd-a1b2'
        >>> generate_task_id(parent_id='bd-a3f8')
        'bd-a3f8.1'
        >>> generate_task_id(parent_id='bd-a3f8.1')
        'bd-a3f8.1.1'
    """
    # Generate random suffix
    suffix = _generate_random_suffix()
    
    if parent_id:
        # Hierarchical ID - append sequence number
        parent_parts = parent_id.split(".")
        if len(parent_parts) == 1:
            # Parent is root level, start at .1
            return f"{parent_id}.1"
        elif len(parent_parts) == 2:
            # Parent is second level (e.g., bd-a3f8.1), increment
            parent_root = parent_parts[0]
            parent_seq = int(parent_parts[1])
            return f"{parent_root}.{parent_seq + 1}"
        else:
            # Three levels deep, can't go deeper
            return parent_id
    else:
        # Root level ID
        return f"{prefix}-{suffix}"


def _generate_random_suffix(length: int = 4) -> str:
    """
    Generate a random alphanumeric suffix.
    
    Uses a limited character set to create readable, short IDs.
    """
    # Use lowercase letters and digits, avoiding ambiguous characters
    chars = "abcdefghijkmnopqrstuvwxyz23456789"
    return "".join(random.choices(chars, k=length))


def parse_task_id(task_id: str) -> dict:
    """
    Parse a task ID into its components.
    
    Args:
        task_id: Task ID to parse (e.g., "bd-a3f8.1.2")
    
    Returns:
        Dictionary with parsed components:
        - prefix: ID prefix (e.g., "bd")
        - root: Root hash (e.g., "a3f8")
        - hierarchy: List of sequence numbers (e.g., [1, 2])
        - is_epic: True if no sequence numbers
    
    Examples:
        >>> parse_task_id("bd-a3f8")
        {'prefix': 'bd', 'root': 'a3f8', 'hierarchy': [], 'is_epic': True}
        >>> parse_task_id("bd-a3f8.1")
        {'prefix': 'bd', 'root': 'a3f8', 'hierarchy': [1], 'is_epic': False}
        >>> parse_task_id("bd-a3f8.1.2")
        {'prefix': 'bd', 'root': 'a3f8', 'hierarchy': [1, 2], 'is_epic': False}
    """
    parts = task_id.split("-")
    if len(parts) != 2:
        raise ValueError(f"Invalid task ID format: {task_id}")
    
    prefix = parts[0]
    rest = parts[1]
    
    # Check for hierarchical parts
    if "." in rest:
        hierarchy_parts = rest.split(".")
        root = hierarchy_parts[0]
        hierarchy = [int(x) for x in hierarchy_parts[1:]]
    else:
        root = rest
        hierarchy = []
    
    return {
        "prefix": prefix,
        "root": root,
        "hierarchy": hierarchy,
        "is_epic": len(hierarchy) == 0,
    }


def get_parent_id(task_id: str) -> Optional[str]:
    """
    Get the parent ID of a hierarchical task.
    
    Args:
        task_id: Task ID (e.g., "bd-a3f8.1.2")
    
    Returns:
        Parent task ID, or None if root level
    
    Examples:
        >>> get_parent_id("bd-a3f8.1")
        'bd-a3f8'
        >>> get_parent_id("bd-a3f8")
        None
    """
    parsed = parse_task_id(task_id)
    
    if parsed["is_epic"]:
        return None
    
    if len(parsed["hierarchy"]) == 1:
        # Single level - parent is the epic
        return f"{parsed['prefix']}-{parsed['root']}"
    
    # Multi-level - parent is all but last level
    parent_parts = [parsed["prefix"], parsed["root"]] + [str(x) for x in parsed["hierarchy"][:-1]]
    return "-".join(parent_parts)


def is_child_of(task_id: str, potential_parent: str) -> bool:
    """
    Check if a task is a descendant of another task.
    
    Args:
        task_id: Task ID to check
        potential_parent: Potential parent ID
    
    Returns:
        True if task_id is a descendant of potential_parent
    """
    parsed = parse_task_id(task_id)
    parent_parsed = parse_task_id(potential_parent)
    
    # Must have same prefix and root
    if parsed["prefix"] != parent_parsed["prefix"]:
        return False
    if parsed["root"] != parent_parsed["root"]:
        return False
    
    # Must have more hierarchy levels than parent
    if len(parsed["hierarchy"]) <= len(parent_parsed["hierarchy"]):
        return False
    
    # Must start with parent's hierarchy
    return parsed["hierarchy"][:len(parent_parsed["hierarchy"])] == parent_parsed["hierarchy"]


def generate_relationship_id(source_id: str, target_id: str, rel_type: str) -> str:
    """
    Generate a unique ID for a relationship.
    
    Args:
        source_id: Source task ID
        target_id: Target task ID
        rel_type: Relationship type
    
    Returns:
        Unique relationship ID
    """
    content = f"{source_id}:{target_id}:{rel_type}"
    hash_suffix = hashlib.md5(content.encode()).hexdigest()[:6]
    return f"rel-{hash_suffix}"
