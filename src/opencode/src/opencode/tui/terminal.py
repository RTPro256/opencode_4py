"""
Terminal capability detection for graceful degradation.

Detects terminal features like color support, Unicode, mouse, etc.
"""

import os
import sys
from dataclasses import dataclass
from typing import Optional


@dataclass
class TerminalCapabilities:
    """Terminal capability information."""
    
    # Color support (0=None, 8=Basic, 256=256-color, 16777216=True color)
    color_level: int = 0
    
    # Unicode support
    unicode: bool = True
    
    # Mouse support
    mouse: bool = True
    
    # Bracketed paste
    bracketed_paste: bool = True
    
    # hyperlinks
    hyperlinks: bool = True
    
    # UTF-8
    utf8: bool = True
    
    # Terminal title
    title: bool = True
    
    # Bell
    bell: bool = True
    
    # Synchronized output (for flicker reduction)
    synchronized_output: bool = False


def get_terminal_capabilities() -> TerminalCapabilities:
    """
    Detect terminal capabilities.
    
    Returns a TerminalCapabilities object with feature flags.
    """
    caps = TerminalCapabilities()
    
    # Check for common CI/headless environments
    if os.environ.get("CI") or os.environ.get("TERM") == "dumb":
        caps.color_level = 0
        caps.unicode = False
        caps.mouse = False
        caps.bracketed_paste = False
        caps.hyperlinks = False
        caps.synchronized_output = False
        return caps
    
    # Check TERM environment variable
    term = os.environ.get("TERM", "")
    
    # Color detection
    caps.color_level = _detect_color_level(term)
    
    # Unicode detection
    caps.unicode = _detect_unicode()
    
    # Mouse detection
    caps.mouse = _detect_mouse(term)
    
    # Bracketed paste
    caps.bracketed_paste = _detect_bracketed_paste(term)
    
    # Hyperlinks (most modern terminals support)
    caps.hyperlinks = term not in ("xterm", "vt100")
    
    # UTF-8 detection
    caps.utf8 = _detect_utf8()
    
    # Title support
    caps.title = term not in ("vt100", "dumb")
    
    # Bell (basic terminal feature)
    caps.bell = True
    
    # Synchronized output (TMUX, modern terminals)
    caps.synchronized_output = _detect_synchronized_output(term)
    
    return caps


def _detect_color_level(term: str) -> int:
    """Detect the color support level."""
    term_lower = term.lower()
    
    # Check for true color / 24-bit color
    if "truecolor" in term_lower or "24bit" in term_lower:
        return 16777216
    
    # Check for 256 colors
    if "256" in term_lower or "xterm" in term_lower:
        return 256
    
    # Check for basic color support
    if term in ("xterm", "screen", "vt100", "rxvt"):
        return 8
    
    # Check environment variables
    if os.environ.get("COLORTERM"):
        if "truecolor" in os.environ["COLORTERM"].lower():
            return 16777216
        if "256" in os.environ["COLORTERM"]:
            return 256
        return 8
    
    # Check for ForceColorTerm
    if os.environ.get("FORCE_COLOR"):
        return 256
    
    return 0


def _detect_unicode() -> bool:
    """Detect Unicode support."""
    # Check if stdout is a TTY or if we're in a known Unicode environment
    if not sys.stdout.isatty() and not os.environ.get("CI"):
        # Non-TTY but check locale
        import locale
        try:
            locale.setlocale(locale.LC_ALL, "")
            encoding = locale.getlocale()[1] or locale.getpreferredencoding()
            return encoding.lower() in ("utf-8", "utf8")
        except locale.Error:
            pass
    
    # Common Unicode-supporting terminals
    term = os.environ.get("TERM", "").lower()
    unicode_terms = ("xterm", "screen", "tmux", "rxvt", "linux", "vt")
    
    return any(t in term for t in unicode_terms)


def _detect_mouse(term: str) -> bool:
    """Detect mouse support."""
    term_lower = term.lower()
    
    # Terminals with mouse support
    mouse_terms = ("xterm", "screen", "tmux", "rxvt", "urxvt", "vt340", "vt420")
    
    return any(t in term_lower for t in mouse_terms)


def _detect_bracketed_paste(term: str) -> bool:
    """Detect bracketed paste support."""
    term_lower = term.lower()
    
    # Most modern terminals support bracketed paste
    paste_terms = ("xterm", "screen", "tmux", "rxvt")
    
    return any(t in term_lower for t in paste_terms)


def _detect_utf8() -> bool:
    """Detect UTF-8 encoding support."""
    # Check Python's encoding
    if sys.stdout.encoding:
        return sys.stdout.encoding.lower().startswith("utf")
    
    # Check locale
    import locale
    try:
        locale.setlocale(locale.LC_ALL, "")
        loc = locale.getlocale()[1]
        if loc:
            return "utf" in loc.lower()
    except locale.Error:
        pass
    
    return False


def _detect_synchronized_output(term: str) -> bool:
    """Detect synchronized output support (for flicker reduction)."""
    term_lower = term.lower()
    
    # TMUX and modern terminals support synchronized output
    sync_terms = ("tmux", "screen-256", "xterm-256")
    
    if any(t in term_lower for t in sync_terms):
        return True
    
    # Check for specific TERM types
    if "tmux" in term_lower:
        return True
    
    # Check environment
    if os.environ.get("TMUX"):
        return True
    
    return False


# Global instance
_terminal_caps: Optional[TerminalCapabilities] = None


def get_terminal() -> TerminalCapabilities:
    """Get cached terminal capabilities."""
    global _terminal_caps
    if _terminal_caps is None:
        _terminal_caps = get_terminal_capabilities()
    return _terminal_caps


def is_color_supported() -> bool:
    """Check if colors are supported."""
    return get_terminal().color_level > 0


def get_color_level() -> int:
    """Get the color support level."""
    return get_terminal().color_level


def supports_truecolor() -> bool:
    """Check if true color (24-bit) is supported."""
    return get_terminal().color_level >= 16777216


def supports_256color() -> bool:
    """Check if 256 colors are supported."""
    return get_terminal().color_level >= 256


def supports_mouse() -> bool:
    """Check if mouse is supported."""
    return get_terminal().mouse


def supports_synchronized_output() -> bool:
    """Check if synchronized output is supported (for flicker reduction)."""
    return get_terminal().synchronized_output
