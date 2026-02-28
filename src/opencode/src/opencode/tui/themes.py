"""
Custom theme system for OpenCode TUI.

Provides modern color themes with CSS custom properties support.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class OpenCodeTheme:
    """Custom theme configuration for OpenCode TUI."""
    
    name: str
    colors: Dict[str, str]


# OpenCode Dark Theme - Modern purple/cyan accent palette
OPENCODE_DARK = OpenCodeTheme(
    name="opencode_dark",
    colors={
        "primary": "#7C3AED",      # Purple accent
        "secondary": "#06B6D4",    # Cyan
        "accent": "#F59E0B",       # Amber
        "success": "#10B981",      # Green
        "warning": "#F59E0B",     # Amber
        "error": "#EF4444",        # Red
        "background": "#1E1E2E",   # Dark background
        "surface": "#2D2D3F",      # Card background
        "panel": "#363647",        # Panel background
        "boost": "#1E1E2E",        # Boost background
        "text": "#E4E4E7",         # Primary text
        "text-muted": "#A1A1AA",   # Secondary text
        "dark": "#121218",         # Darker areas
        "light": "#E4E4E7",        # Light text
    },
)


# OpenCode Light Theme
OPENCODE_LIGHT = OpenCodeTheme(
    name="opencode_light",
    colors={
        "primary": "#7C3AED",      # Purple accent
        "secondary": "#0891B2",   # Cyan darker
        "accent": "#D97706",       # Amber darker
        "success": "#059669",      # Green darker
        "warning": "#D97706",      # Amber darker
        "error": "#DC2626",        # Red darker
        "background": "#FAFAFA",   # Light background
        "surface": "#F4F4F5",      # Card background
        "panel": "#E4E4E7",        # Panel background
        "boost": "#FFFFFF",        # Boost background
        "text": "#27272A",         # Primary text
        "text-muted": "#71717A",   # Secondary text
        "dark": "#18181B",         # Dark areas
        "light": "#FAFAFA",        # Light text
    },
)


# Catppuccin Mocha inspired theme
OPENCODE_CATPPUCCIN = OpenCodeTheme(
    name="opencode_catppuccin",
    colors={
        "primary": "#CBA6F7",      # Mauve
        "secondary": "#89DCEB",    # Sky
        "accent": "#FAB387",       # Peach
        "success": "#A6E3A1",       # Green
        "warning": "#F9E2AF",       # Yellow
        "error": "#F38BA8",         # Red
        "background": "#11111B",    # Base
        "surface": "#1E1E2E",      # Surface0
        "panel": "#313244",        # Surface1
        "boost": "#11111B",        # Base
        "text": "#CDD6F4",          # Text
        "text-muted": "#A6ADC8",   # Subtext0
        "dark": "#0D0D14",         # Mantle
        "light": "#EFF1F5",        # Crust
    },
)


# Nord-inspired theme
OPENCODE_NORD = OpenCodeTheme(
    name="opencode_nord",
    colors={
        "primary": "#88C0D0",      # Frost cyan
        "secondary": "#81A1C1",     # Frost blue
        "accent": "#D8DEE9",        # Snow storm
        "success": "#A3BE8C",      # Aurora green
        "warning": "#EBCB8B",       # Aurora yellow
        "error": "#BF616A",        # Aurora red
        "background": "#2E3440",    # Polar night dark
        "surface": "#3B4252",      # Polar night medium
        "panel": "#434C5E",        # Polar night light
        "boost": "#2E3440",        # Polar night dark
        "text": "#ECEFF4",         # Snow storm white
        "text-muted": "#D8DEE9",  # Snow storm gray
        "dark": "#242933",         # Darker
        "light": "#E5E9F0",        # Lighter
    },
)


# Theme registry
THEMES: Dict[str, OpenCodeTheme] = {
    "dark": OPENCODE_DARK,
    "light": OPENCODE_LIGHT,
    "catppuccin": OPENCODE_CATPPUCCIN,
    "nord": OPENCODE_NORD,
}


def get_theme(name: str) -> OpenCodeTheme:
    """Get a theme by name, defaulting to dark."""
    return THEMES.get(name, OPENCODE_DARK)


def get_theme_names() -> list[str]:
    """Get list of available theme names."""
    return list(THEMES.keys())


# CSS Custom Properties for enhanced styling
# These are added to the app's CSS
OPENCODE_CSS_VARS = """
/* OpenCode CSS Custom Properties */
:root {
    /* Primary accent colors */
    --opencode-primary: #7C3AED;
    --opencode-secondary: #06B6D4;
    --opencode-accent: #F59E0B;
    
    /* Status colors */
    --opencode-success: #10B981;
    --opencode-warning: #F59E0B;
    --opencode-error: #EF4444;
    
    /* Message bubble colors */
    --opencode-user-bg: #7C3AED;
    --opencode-assistant-bg: #2D2D3F;
    --opencode-system-bg: #F59E0B;
    --opencode-tool-bg: #06B6D4;
    
    /* Typography */
    --opencode-font-mono: 'Cascadia Code', 'Fira Code', 'JetBrains Mono', monospace;
    
    /* Spacing */
    --opencode-spacing-xs: 2;
    --opencode-spacing-sm: 4;
    --opencode-spacing-md: 8;
    --opencode-spacing-lg: 16;
    --opencode-spacing-xl: 24;
    
    /* Border radius */
    --opencode-radius-sm: 4;
    --opencode-radius-md: 8;
    --opencode-radius-lg: 12;
    
    /* Animation durations */
    --opencode-animate-fast: 0.1s;
    --opencode-animate-normal: 0.2s;
    --opencode-animate-slow: 0.3s;
}

/* Dark theme specific */
.opencode-dark {
    --opencode-bg: #1E1E2E;
    --opencode-surface: #2D2D3F;
    --opencode-text: #E4E4E7;
    --opencode-text-muted: #A1A1AA;
}

/* Light theme specific */
.opencode-light {
    --opencode-bg: #FAFAFA;
    --opencode-surface: #F4F4F5;
    --opencode-text: #27272A;
    --opencode-text-muted: #71717A;
}
"""
