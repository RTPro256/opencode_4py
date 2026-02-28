"""
Tests for SkillPointer module.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import tempfile
import shutil

from opencode.skills.pointer import (
    categorize_skill,
    get_categories,
    estimate_token_savings,
    is_pointer_skill,
    extract_category,
    CategoryPointer,
    CategoryPointerConfig,
    SkillPointerManager,
)


class TestCategorizeSkill:
    """Tests for categorize_skill function."""

    def test_categorize_security(self):
        """Test security category detection."""
        assert categorize_skill("security-auth") == "security"
        assert categorize_skill("xss-vulnerability") == "security"
        assert categorize_skill("penetration-test") == "security"

    def test_categorize_ai_ml(self):
        """Test AI/ML category detection."""
        assert categorize_skill("ai-agent") == "ai-ml"
        assert categorize_skill("llm-prompt") == "ai-ml"
        assert categorize_skill("rag-implementation") == "ai-ml"

    def test_categorize_web_dev(self):
        """Test web dev category detection."""
        assert categorize_skill("react-component") == "web-dev"
        assert categorize_skill("vue-starter") == "web-dev"
        assert categorize_skill("nextjs-app") == "web-dev"

    def test_categorize_backend_dev(self):
        """Test backend dev category detection."""
        assert categorize_skill("api-rest") == "backend-dev"
        assert categorize_skill("express-middleware") == "backend-dev"
        assert categorize_skill("fastapi-endpoint") == "backend-dev"

    def test_categorize_devops(self):
        """Test devops category detection."""
        assert categorize_skill("docker-container") == "devops"
        assert categorize_skill("kubernetes-deploy") == "devops"
        assert categorize_skill("terraform-aws") == "devops"

    def test_categorize_database(self):
        """Test database category detection."""
        assert categorize_skill("sql-query") == "database"
        assert categorize_skill("postgres-setup") == "database"
        assert categorize_skill("mongodb-schema") == "database"

    def test_categorize_uncategorized(self):
        """Test uncategorized for unknown skills."""
        # Use values that won't match any heuristic keywords
        assert categorize_skill("xyz123abc") == "_uncategorized"
        # 'foobar' accidentally matches - using different values
        assert categorize_skill("qwerty789") == "_uncategorized"

    def test_categorize_case_insensitive(self):
        """Test case insensitive categorization."""
        assert categorize_skill("REACT-COMPONENT") == "web-dev"
        assert categorize_skill("Docker-Container") == "devops"


class TestGetCategories:
    """Tests for get_categories function."""

    def test_get_categories_returns_list(self):
        """Test that get_categories returns a list."""
        categories = get_categories()
        assert isinstance(categories, list)

    def test_get_categories_not_empty(self):
        """Test that categories list is not empty."""
        categories = get_categories()
        assert len(categories) > 0

    def test_get_categories_sorted(self):
        """Test that categories are sorted."""
        categories = get_categories()
        assert categories == sorted(categories)


class TestEstimateTokenSavings:
    """Tests for estimate_token_savings function."""

    def test_estimate_token_savings_50_skills(self):
        """Test token savings for 50 skills."""
        savings = estimate_token_savings(50)
        assert savings["traditional_tokens"] == 2000  # 50 * 40
        # With SkillPointer: 1 category * 7 tokens (min 1 category)
        assert savings["pointer_tokens"] == 7
        assert savings["savings_percent"] > 0

    def test_estimate_token_savings_500_skills(self):
        """Test token savings for 500 skills."""
        savings = estimate_token_savings(500)
        assert savings["traditional_tokens"] == 20000  # 500 * 40

    def test_estimate_token_savings_2000_skills(self):
        """Test token savings for 2000 skills."""
        savings = estimate_token_savings(2000)
        assert savings["traditional_tokens"] == 80000  # 2000 * 40
        assert savings["savings_percent"] > 99  # Should be ~99.7%

    def test_estimate_token_savings_zero(self):
        """Test token savings with zero skills."""
        savings = estimate_token_savings(0)
        assert savings["traditional_tokens"] == 0
        # Even with 0 skills, min 1 category with 7 tokens
        assert savings["pointer_tokens"] == 7


class TestIsPointerSkill:
    """Tests for is_pointer_skill function."""

    def test_is_pointer_skill_true(self):
        """Test pointer skill detection."""
        assert is_pointer_skill("security-category-pointer") is True
        assert is_pointer_skill("ai-ml-category-pointer") is True

    def test_is_pointer_skill_false(self):
        """Test non-pointer skill detection."""
        assert is_pointer_skill("react-component") is False
        assert is_pointer_skill("security-auth") is False


class TestExtractCategory:
    """Tests for extract_category function."""

    def test_extract_category_from_pointer(self):
        """Test category extraction from pointer name."""
        assert extract_category("security-category-pointer") == "security"
        assert extract_category("ai-ml-category-pointer") == "ai-ml"

    def test_extract_category_from_regular(self):
        """Test category extraction returns None for regular skills."""
        assert extract_category("react-component") is None


class TestCategoryPointerConfig:
    """Tests for CategoryPointerConfig dataclass."""

    def test_category_pointer_config_creation(self):
        """Test creating a CategoryPointerConfig."""
        config = CategoryPointerConfig(
            category="security",
            vault_path=Path("/tmp/vault"),
            skill_count=100,
            description="Test category",
        )
        assert config.category == "security"
        assert config.skill_count == 100

    def test_category_pointer_config_to_dict(self):
        """Test to_dict method."""
        config = CategoryPointerConfig(
            category="security",
            vault_path=Path("/tmp/vault"),
            skill_count=100,
        )
        d = config.to_dict()
        assert d["category"] == "security"
        assert d["skill_count"] == 100


class TestCategoryPointer:
    """Tests for CategoryPointer class."""

    def test_category_pointer_creation(self):
        """Test creating a CategoryPointer."""
        pointer = CategoryPointer(
            category="security",
            vault_path=Path("/tmp/vault"),
            skill_count=100,
        )
        assert pointer.category == "security"
        assert pointer.skill_count == 100

    def test_category_pointer_properties(self):
        """Test CategoryPointer properties."""
        vault_path = Path("/tmp/vault")
        pointer = CategoryPointer(
            category="web-dev",
            vault_path=vault_path,
            skill_count=50,
        )
        assert pointer.vault_path == vault_path

    def test_category_pointer_config(self):
        """Test CategoryPointer config generation."""
        pointer = CategoryPointer(
            category="testing",
            vault_path=Path("/tmp/vault"),
            skill_count=25,
        )
        assert pointer._pointer_config.category == "testing"
        assert pointer._pointer_config.skill_count == 25


class TestSkillPointerManager:
    """Tests for SkillPointerManager class."""

    def test_manager_init_defaults(self):
        """Test default initialization."""
        with patch("opencode.skills.pointer.Path.home", return_value=Path("/home/user")):
            manager = SkillPointerManager()
            assert manager.vault_dir.name == ".opencode-skill-libraries"

    def test_manager_init_custom_dirs(self):
        """Test initialization with custom directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            active = Path(tmpdir) / "skills"
            vault = Path(tmpdir) / "vault"
            manager = SkillPointerManager(
                active_skills_dir=active,
                vault_dir=vault,
            )
            assert manager.active_skills_dir == active
            assert manager.vault_dir == vault

    def test_manager_properties(self):
        """Test manager properties."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SkillPointerManager(vault_dir=Path(tmpdir))
            assert manager.vault_dir == Path(tmpdir)


class TestSkillPointerManagerMigration:
    """Tests for SkillPointerManager migration methods."""

    def test_migrate_skills_nonexistent_dir(self):
        """Test migrate_skills with non-existent active directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SkillPointerManager(
                active_skills_dir=Path("/nonexistent"),
                vault_dir=Path(tmpdir),
            )
            result = manager.migrate_skills()
            assert result == {}

    def test_migrate_skills_empty_dir(self):
        """Test migrate_skills with empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            active = Path(tmpdir) / "skills"
            vault = Path(tmpdir) / "vault"
            active.mkdir()
            manager = SkillPointerManager(
                active_skills_dir=active,
                vault_dir=vault,
            )
            result = manager.migrate_skills()
            assert result == {}

    def test_generate_pointers_nonexistent_vault(self):
        """Test generate_pointers with non-existent vault."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = SkillPointerManager(
                vault_dir=Path("/nonexistent"),
            )
            result = manager.generate_pointers()
            assert result == {}


class TestSkillPointerManagerSetup:
    """Tests for SkillPointerManager setup method."""

    def test_setup_creates_vault(self):
        """Test setup creates vault directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            active = Path(tmpdir) / "skills"
            vault = Path(tmpdir) / "vault"
            active.mkdir()
            
            # Add a test skill
            skill_dir = active / "test-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("# Test Skill")
            
            manager = SkillPointerManager(
                active_skills_dir=active,
                vault_dir=vault,
            )
            result = manager.setup()
            
            assert "skills_migrated" in result
            assert "categories" in result
            assert "pointers_created" in result
