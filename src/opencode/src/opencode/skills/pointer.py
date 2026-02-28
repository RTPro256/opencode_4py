"""
SkillPointer Module

This module provides the SkillPointer pattern for organizing large skill libraries.
It solves the "Token Tax" problem where having hundreds or thousands of skills
causes significant startup token overhead.

The SkillPointer architecture:
1. Category Pointers - Lightweight skills that index entire categories
2. Hidden Vault - Skills stored outside the scanner path
3. Dynamic Retrieval - AI uses native tools to browse the vault

Usage:
    from opencode.skills.pointer import SkillPointer, categorize_skill
    
    # Categorize a skill
    category = categorize_skill("react-button-component")
    # Returns: "web-dev"
"""

import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from opencode.skills.models import Skill, SkillConfig, SkillType, SkillStatus

logger = logging.getLogger(__name__)

# =============================================================================
# Heuristic Engine for Categorization
# =============================================================================

DOMAIN_HEURISTICS: Dict[str, List[str]] = {
    "security": [
        "attack", "injection", "vulnerability", "xss", "penetration", "privilege",
        "fuzzing", "auth", "jwt", "oauth", "bypass", "malware", "forensics",
        "hacker", "wireshark", "nmap", "security", "exploit", "encryption",
    ],
    "ai-ml": [
        "ai-", "ml-", "llm", "agent", "gpt", "claude", "gemini", "openai",
        "anthropic", "prompt", "rag", "diffusion", "huggingface", "pytorch",
        "tensorflow", "comfy", "flux", "machine-learning", "deep-learning",
        "vision", "nlp",
    ],
    "web-dev": [
        "angular", "react", "vue", "tailwind", "frontend", "css", "html",
        "nextjs", "svelte", "astro", "web", "dom", "ui-patterns", "vercel",
        "shopify", "styles", "sass", "less", "bootstrap",
    ],
    "backend-dev": [
        "api", "nestjs", "express", "django", "flask", "fastapi", "spring",
        "laravel", "node", "graphql", "rest", "grpc", "backend", "server",
        "microservice", "go-", "rust-",
    ],
    "devops": [
        "aws", "azure", "docker", "kubernetes", "ci-cd", "terraform", "ansible",
        "github-actions", "gitlab", "jenkins", "devops", "cloud", "linux",
        "ubuntu", "k8s", "bash", "deploy", "nginx",
    ],
    "database": [
        "sql", "mysql", "postgres", "mongo", "redis", "database", "schema",
        "prisma", "orm", "nosql", "supabase", "neon", "db-", "sqlite",
    ],
    "design": [
        "ui", "ux", "design", "figma", "avatar", "background-removal", "svg",
        "animation", "motion", "framer", "photoshop", "illustrator", "creative",
    ],
    "automation": [
        "automation", "zapier", "make", "n8n", "selenium", "playwright",
        "puppeteer", "bot", "workflow", "scraper", "cron",
    ],
    "mobile": [
        "ios", "android", "react-native", "flutter", "swift", "kotlin",
        "mobile", "xcode", "mobile-",
    ],
    "game-dev": [
        "game", "unity", "unreal", "godot", "phaser", "3d", "vr", "ar",
        "raylib", "pygame",
    ],
    "business": [
        "business", "founder", "sales", "marketing", "seo", "growth", "product",
        "agile", "scrum", "jira", "b2b", "crm",
    ],
    "writing": [
        "writing", "copywriting", "blog", "documentation", "readme", "study",
        "teardown", "content", "journalism",
    ],
    "3d-graphics": [
        "blender", "threejs", "webgl", "rendering", "3d-", "mesh", "texture",
        "shader",
    ],
    "aerospace": [
        "satellite", "orbit", "space", "aerodynamics", "avionic", "spacecraft",
    ],
    "agents": [
        "multi-agent", "swarm", "autonomous", "orchestration", "chain",
        "autogen", "crewai",
    ],
    "animation": [
        "gsap", "lottie", "keyframe", "transition", "tween", "rigging",
    ],
    "architecture": [
        "pattern", "clean-code", "system-design", "solid-", "ddd", "architect",
    ],
    "biomedical": [
        "dna", "protein", "medical", "health", "genomics", "bioinfo", "clinical",
    ],
    "blockchain": [
        "crypto", "web3", "solidity", "smart-contract", "ethereum", "bitcoin",
        "nft", "staking",
    ],
    "compliance": [
        "gdpr", "hipaa", "soc2", "audit", "policy", "legal", "privacy",
    ],
    "data-science": [
        "pandas", "numpy", "matplotlib", "scikit", "jupyter", "visualization",
        "data-", "etl",
    ],
    "education": [
        "learning", "course", "tutor", "student", "curriculum", "teaching",
        "university",
    ],
    "finance": [
        "trading", "stock", "portfolio", "banking", "ledger", "investment",
        "fintech",
    ],
    "marketing": [
        "ads", "campaign", "social-media", "brand", "analytics", "funnel",
        "email-marketing",
    ],
    "mcp": [
        "mcp-", "model-context-protocol", "server-", "client-",
    ],
    "media-production": [
        "video", "audio", "podcast", "editing", "streaming", "ffmpeg", "obs",
    ],
    "programming": [
        "python", "javascript", "typescript", "java", "cpp", "ruby", "php",
        "csharp", "swift", "kotlin", "algorithm", "data-structure",
    ],
    "prompt-engineering": [
        "system-prompt", "few-shot", "chain-of-thought", "prompt-", "meta-prompt",
    ],
    "quantum": [
        "qubit", "qiskit", "quantum-", "superposition", "entanglement",
    ],
    "robotics": [
        "ros", "arduino", "raspberry", "hardware", "sensor", "firmware", "robot",
    ],
    "simulation": [
        "physics", "modeling", "sim-", "digital-twin", "solver",
    ],
    "testing": [
        "test-", "unit-test", "jest", "pytest", "cypress", "quality", "qa-",
    ],
    "tooling": [
        "cli", "prettier", "eslint", "bundler", "npm", "pip", "extension", "plugin",
    ],
}


def categorize_skill(skill_name: str) -> str:
    """
    Categorize a skill using keyword heuristics.
    
    Args:
        skill_name: Name of the skill to categorize
        
    Returns:
        Category name (e.g., "web-dev", "security", "ai-ml")
        Returns "_uncategorized" if no match found
    """
    name_lower = skill_name.lower().replace("_", "-")
    
    for category, keywords in DOMAIN_HEURISTICS.items():
        if any(kw in name_lower for kw in keywords):
            return category
    
    return "_uncategorized"


def get_categories() -> List[str]:
    """Get list of all available categories."""
    return sorted(DOMAIN_HEURISTICS.keys())


# =============================================================================
# Category Pointer Models
# =============================================================================

@dataclass
class CategoryPointerConfig:
    """Configuration for a category pointer."""
    category: str
    vault_path: Path
    skill_count: int = 0
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "vault_path": str(self.vault_path),
            "skill_count": self.skill_count,
            "description": self.description,
        }


class CategoryPointer(Skill):
    """
    A category pointer skill that indexes a category of skills in the vault.
    
    Instead of loading all skill descriptions at startup, the AI matches
    a category pointer and then browses the vault to find specific skills.
    """
    
    def __init__(
        self,
        category: str,
        vault_path: Path,
        skill_count: int = 0,
        **kwargs,
    ):
        category_title = category.replace("-", " ").title()
        
        config = SkillConfig(
            name=f"{category}-category-pointer",
            description=f"Triggers when encountering any task related to {category_title}. This is a pointer to a library of specialized skills.",
            skill_type=SkillType.PROMPT,
            trigger=f"/{category}",
            template=self._generate_template(category, category_title, vault_path, skill_count),
        )
        
        super().__init__(
            config=config,
            **kwargs,
        )
        
        self._category = category
        self._vault_path = vault_path
        self._skill_count = skill_count
        self._pointer_config = CategoryPointerConfig(
            category=category,
            vault_path=vault_path,
            skill_count=skill_count,
        )
    
    @property
    def category(self) -> str:
        """Get the category name."""
        return self._category
    
    @property
    def vault_path(self) -> Path:
        """Get the vault path for this category."""
        return self._vault_path
    
    @property
    def skill_count(self) -> int:
        """Get the number of skills in this category."""
        return self._skill_count
    
    def _generate_template(
        self,
        category: str,
        category_title: str,
        vault_path: Path,
        skill_count: int,
    ) -> str:
        """Generate the pointer instruction template."""
        # Use relative path with environment variable for portability
        # The vault is typically at ~/.opencode-skill-libraries/
        vault_str = f"$HOME/.opencode-skill-libraries/{category}"
        
        # Also include the absolute path as fallback for local reference
        abs_path = str(vault_path.absolute()).replace("\\", "/")
        
        return f"""# {category_title} Capability Library 🎯

You do not have all {category_title} skills loaded immediately in your background context. Instead, you have access to a rich library of {skill_count} highly-specialized skills on your local filesystem.

## Instructions
1. When you need to perform a task related to {category}, you MUST use your file reading tools (like `list_dir` and `view_file` or `read_file`) to browse the hidden library directory: `{vault_str}` (or `{abs_path}` locally)
2. Locate the specific Markdown files related to the exact sub-task you need.
3. Read the relevant Markdown file(s) into your context.
4. Follow the specific instructions and best practices found within those files to complete the user's request.

## Available Knowledge
This library contains {skill_count} specialized skills covering various aspects of {category_title}.

**Hidden Library Path:** `{vault_str}`

*Reminder: Do not guess best practices or blindly search GitHub. Always consult your local library files first.*"""


# =============================================================================
# SkillPointer Manager
# =============================================================================

class SkillPointerManager:
    """
    Manages the SkillPointer architecture for large skill libraries.
    
    This class handles:
    - Converting skills to pointer architecture
    - Managing the hidden vault
    - Generating category pointers
    - Token optimization
    """
    
    DEFAULT_VAULT_DIR = Path.home() / ".opencode-skill-libraries"
    
    def __init__(
        self,
        active_skills_dir: Optional[Path] = None,
        vault_dir: Optional[Path] = None,
    ):
        """
        Initialize the SkillPointer manager.
        
        Args:
            active_skills_dir: Directory containing active skills (default: ~/.config/opencode/skills)
            vault_dir: Directory for hidden skill vault (default: ~/.opencode-skill-libraries)
        """
        self._active_skills_dir = active_skills_dir or (
            Path.home() / ".config" / "opencode" / "skills"
        )
        self._vault_dir = vault_dir or self.DEFAULT_VAULT_DIR
        self._categories: Dict[str, CategoryPointer] = {}
    
    @property
    def vault_dir(self) -> Path:
        """Get the vault directory."""
        return self._vault_dir
    
    @property
    def active_skills_dir(self) -> Path:
        """Get the active skills directory."""
        return self._active_skills_dir
    
    def migrate_skills(
        self,
        categories: Optional[Dict[str, List[str]]] = None,
    ) -> Dict[str, int]:
        """
        Migrate skills from active directory to vault.
        
        Args:
            categories: Optional dict mapping categories to skill names
                       If None, skills will be auto-categorized
            
        Returns:
            Dict mapping categories to number of skills migrated
        """
        if not self._active_skills_dir.exists():
            logger.warning(f"Active skills directory not found: {self._active_skills_dir}")
            return {}
        
        # Ensure vault exists
        self._vault_dir.mkdir(parents=True, exist_ok=True)
        
        category_counts: Dict[str, int] = {}
        moved_count = 0
        
        for folder in list(self._active_skills_dir.iterdir()):
            if not folder.is_dir():
                continue
            
            # Ignore existing pointers
            if folder.name.endswith("-category-pointer"):
                continue
            
            # Ignore empty folders
            if not any(folder.iterdir()):
                continue
            
            # Determine category
            if categories:
                category = None
                for cat, skills in categories.items():
                    if folder.name in skills:
                        category = cat
                        break
                if not category:
                    category = "_uncategorized"
            else:
                category = categorize_skill(folder.name)
            
            # Move to vault
            cat_dir = self._vault_dir / category
            cat_dir.mkdir(parents=True, exist_ok=True)
            
            dest = cat_dir / folder.name
            if dest.exists():
                shutil.rmtree(dest)
            
            shutil.move(str(folder), str(cat_dir))
            
            category_counts[category] = category_counts.get(category, 0) + 1
            moved_count += 1
            logger.debug(f"Migrated '{folder.name}' -> {category}/")
        
        logger.info(f"Migrated {moved_count} skills to vault at {self._vault_dir}")
        return category_counts
    
    def generate_pointers(self) -> Dict[str, CategoryPointer]:
        """
        Generate category pointers for all categories in the vault.
        
        Returns:
            Dict mapping category names to CategoryPointer objects
        """
        if not self._vault_dir.exists():
            logger.warning(f"Vault directory not found: {self._vault_dir}")
            return {}
        
        pointers: Dict[str, CategoryPointer] = {}
        
        for cat_dir in self._vault_dir.iterdir():
            if not cat_dir.is_dir():
                continue
            
            cat = cat_dir.name
            
            # Count SKILL.md files
            count = sum(1 for p in cat_dir.rglob("SKILL.md"))
            if count == 0:
                continue
            
            # Create pointer
            pointer = CategoryPointer(
                category=cat,
                vault_path=cat_dir,
                skill_count=count,
            )
            
            pointers[cat] = pointer
            logger.debug(f"Created pointer for '{cat}' with {count} skills")
        
        self._categories = pointers
        logger.info(f"Generated {len(pointers)} category pointers")
        return pointers
    
    def save_pointers(self) -> int:
        """
        Save category pointers to active skills directory.
        
        Returns:
            Number of pointers saved
        """
        if not self._categories:
            self.generate_pointers()
        
        saved = 0
        for cat, pointer in self._categories.items():
            pointer_name = f"{cat}-category-pointer"
            pointer_dir = self._active_skills_dir / pointer_name
            pointer_dir.mkdir(parents=True, exist_ok=True)
            
            # Write SKILL.md
            skill_file = pointer_dir / "SKILL.md"
            skill_file.write_text(pointer.config.template, encoding="utf-8")
            
            saved += 1
            logger.debug(f"Saved pointer: {pointer_name}")
        
        logger.info(f"Saved {saved} pointers to {self._active_skills_dir}")
        return saved
    
    def setup(self) -> Dict[str, Any]:
        """
        Complete setup: migrate skills and generate pointers.
        
        Returns:
            Dict with migration and pointer statistics
        """
        # Migrate skills
        category_counts = self.migrate_skills()
        
        # Generate pointers
        pointers = self.generate_pointers()
        
        # Save pointers
        saved = self.save_pointers()
        
        total_skills = sum(category_counts.values())
        
        return {
            "skills_migrated": total_skills,
            "categories": len(category_counts),
            "pointers_created": saved,
            "vault_path": str(self._vault_dir),
        }
    
    def get_pointer(self, category: str) -> Optional[CategoryPointer]:
        """Get pointer for a specific category."""
        if not self._categories:
            self.generate_pointers()
        return self._categories.get(category)
    
    def list_categories(self) -> List[str]:
        """List all available categories."""
        if not self._categories:
            self.generate_pointers()
        return list(self._categories.keys())
    
    def get_vault_skills(self, category: str) -> List[Path]:
        """Get all skill files in a category vault."""
        cat_dir = self._vault_dir / category
        if not cat_dir.exists():
            return []
        
        return list(cat_dir.rglob("SKILL.md"))


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class SkillPointerConfig:
    """Configuration for SkillPointer integration."""
    enabled: bool = False
    vault_path: Path = field(default_factory=lambda: SkillPointerManager.DEFAULT_VAULT_DIR)
    active_skills_dir: Optional[Path] = None
    threshold: int = 50  # Use pointers when > threshold skills
    auto_categorize: bool = True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillPointerConfig":
        """Create from dictionary."""
        return cls(
            enabled=data.get("enabled", False),
            vault_path=Path(data.get("vault_path", SkillPointerManager.DEFAULT_VAULT_DIR)),
            active_skills_dir=Path(data["active_skills_dir"]) if data.get("active_skills_dir") else None,
            threshold=data.get("threshold", 50),
            auto_categorize=data.get("auto_categorize", True),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "enabled": self.enabled,
            "vault_path": str(self.vault_path),
            "active_skills_dir": str(self.active_skills_dir) if self.active_skills_dir else None,
            "threshold": self.threshold,
            "auto_categorize": self.auto_categorize,
        }


# =============================================================================
# Utility Functions
# =============================================================================

def estimate_token_savings(num_skills: int, avg_desc_length: int = 40) -> Dict[str, Any]:
    """
    Estimate token savings from using SkillPointer.
    
    Args:
        num_skills: Number of skills in the library
        avg_desc_length: Average description length in tokens
        
    Returns:
        Dict with token estimates
    """
    # Traditional: all skill descriptions at startup
    traditional_tokens = num_skills * avg_desc_length
    
    # With SkillPointer: ~35 category pointers * ~7 tokens each
    num_categories = min(35, max(1, num_skills // 50))
    pointer_tokens = num_categories * 7
    
    savings = traditional_tokens - pointer_tokens
    savings_percent = (savings / traditional_tokens * 100) if traditional_tokens > 0 else 0
    
    return {
        "num_skills": num_skills,
        "traditional_tokens": traditional_tokens,
        "pointer_tokens": pointer_tokens,
        "savings_tokens": savings,
        "savings_percent": savings_percent,
    }


def is_pointer_skill(skill_name: str) -> bool:
    """Check if a skill name is a category pointer."""
    return skill_name.endswith("-category-pointer")


def extract_category(pointer_name: str) -> Optional[str]:
    """Extract category name from a pointer skill name."""
    if not pointer_name.endswith("-category-pointer"):
        return None
    return pointer_name.replace("-category-pointer", "")
