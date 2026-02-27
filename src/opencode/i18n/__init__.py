"""Internationalization (i18n) module for OpenCode."""

from .manager import I18nManager, get_i18n, set_language, t, _

__all__ = [
    "I18nManager",
    "get_i18n",
    "set_language",
    "t",
    "_",
]
