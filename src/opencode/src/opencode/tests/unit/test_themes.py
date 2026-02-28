"""
Tests for themes module.
"""

import pytest
from opencode.tui.themes import (
    OpenCodeTheme,
    OPENCODE_DARK,
    OPENCODE_LIGHT,
    OPENCODE_CATPPUCCIN,
    OPENCODE_NORD,
    THEMES,
    get_theme,
    get_theme_names,
    OPENCODE_CSS_VARS,
)


class TestOpenCodeTheme:
    """Tests for OpenCodeTheme dataclass."""

    def test_theme_creation(self):
        """Test creating a theme."""
        theme = OpenCodeTheme(
            name="test_theme",
            colors={"primary": "#FF0000", "background": "#000000"},
        )
        assert theme.name == "test_theme"
        assert theme.colors["primary"] == "#FF0000"

    def test_theme_colors_dict(self):
        """Test theme colors is a dict."""
        assert isinstance(OPENCODE_DARK.colors, dict)
        assert len(OPENCODE_DARK.colors) > 0


class TestPredefinedThemes:
    """Tests for predefined themes."""

    def test_opencode_dark_exists(self):
        """Test dark theme exists."""
        assert OPENCODE_DARK.name == "opencode_dark"
        assert "primary" in OPENCODE_DARK.colors
        assert "background" in OPENCODE_DARK.colors

    def test_opencode_light_exists(self):
        """Test light theme exists."""
        assert OPENCODE_LIGHT.name == "opencode_light"
        assert "primary" in OPENCODE_LIGHT.colors
        assert "background" in OPENCODE_LIGHT.colors

    def test_opencode_catppuccin_exists(self):
        """Test catppuccin theme exists."""
        assert OPENCODE_CATPPUCCIN.name == "opencode_catppuccin"
        assert "primary" in OPENCODE_CATPPUCCIN.colors

    def test_opencode_nord_exists(self):
        """Test nord theme exists."""
        assert OPENCODE_NORD.name == "opencode_nord"
        assert "primary" in OPENCODE_NORD.colors


class TestThemeRegistry:
    """Tests for theme registry."""

    def test_themes_dict_exists(self):
        """Test THEMES dict exists."""
        assert isinstance(THEMES, dict)

    def test_themes_contains_dark(self):
        """Test dark theme in registry."""
        assert "dark" in THEMES

    def test_themes_contains_light(self):
        """Test light theme in registry."""
        assert "light" in THEMES

    def test_themes_contains_catppuccin(self):
        """Test catppuccin theme in registry."""
        assert "catppuccin" in THEMES

    def test_themes_contains_nord(self):
        """Test nord theme in registry."""
        assert "nord" in THEMES

    def test_themes_has_four_themes(self):
        """Test that there are four themes."""
        assert len(THEMES) == 4


class TestGetTheme:
    """Tests for get_theme function."""

    def test_get_dark_theme(self):
        """Test getting dark theme."""
        theme = get_theme("dark")
        assert theme.name == "opencode_dark"

    def test_get_light_theme(self):
        """Test getting light theme."""
        theme = get_theme("light")
        assert theme.name == "opencode_light"

    def test_get_catppuccin_theme(self):
        """Test getting catppuccin theme."""
        theme = get_theme("catppuccin")
        assert theme.name == "opencode_catppuccin"

    def test_get_nord_theme(self):
        """Test getting nord theme."""
        theme = get_theme("nord")
        assert theme.name == "opencode_nord"

    def test_get_unknown_theme_defaults_to_dark(self):
        """Test getting unknown theme returns dark."""
        theme = get_theme("nonexistent")
        assert theme.name == "opencode_dark"

    def test_get_theme_case_sensitive(self):
        """Test theme lookup is case sensitive."""
        theme = get_theme("Dark")
        assert theme.name == "opencode_dark"


class TestGetThemeNames:
    """Tests for get_theme_names function."""

    def test_get_theme_names_returns_list(self):
        """Test get_theme_names returns a list."""
        names = get_theme_names()
        assert isinstance(names, list)

    def test_get_theme_names_contains_expected(self):
        """Test theme names contains expected values."""
        names = get_theme_names()
        assert "dark" in names
        assert "light" in names
        assert "catppuccin" in names
        assert "nord" in names


class TestThemeColors:
    """Tests for theme color values."""

    def test_dark_primary_is_purple(self):
        """Test dark theme primary color."""
        assert OPENCODE_DARK.colors["primary"] == "#7C3AED"

    def test_light_primary_is_purple(self):
        """Test light theme primary color."""
        assert OPENCODE_LIGHT.colors["primary"] == "#7C3AED"

    def test_catppuccin_primary_is_mauve(self):
        """Test catppuccin primary color."""
        assert OPENCODE_CATPPUCCIN.colors["primary"] == "#CBA6F7"

    def test_nord_primary_is_cyan(self):
        """Test nord primary color."""
        assert OPENCODE_NORD.colors["primary"] == "#88C0D0"

    def test_all_themes_have_required_colors(self):
        """Test all themes have required color keys."""
        required_keys = {"primary", "secondary", "accent", "success", "warning", "error", "background", "surface", "text"}
        
        for theme_name, theme in THEMES.items():
            missing_keys = required_keys - set(theme.colors.keys())
            assert not missing_keys, f"Theme {theme_name} missing keys: {missing_keys}"


class TestCssVars:
    """Tests for CSS custom properties."""

    def test_css_vars_exists(self):
        """Test CSS vars string exists."""
        assert isinstance(OPENCODE_CSS_VARS, str)
        assert len(OPENCODE_CSS_VARS) > 0

    def test_css_vars_contains_root(self):
        """Test CSS vars contains :root."""
        assert ":root" in OPENCODE_CSS_VARS

    def test_css_vars_contains_custom_props(self):
        """Test CSS vars contains custom properties."""
        assert "--opencode-primary" in OPENCODE_CSS_VARS
        assert "--opencode-secondary" in OPENCODE_CSS_VARS

    def test_css_vars_contains_dark_class(self):
        """Test CSS vars contains dark theme class."""
        assert ".opencode-dark" in OPENCODE_CSS_VARS

    def test_css_vars_contains_light_class(self):
        """Test CSS vars contains light theme class."""
        assert ".opencode-light" in OPENCODE_CSS_VARS
