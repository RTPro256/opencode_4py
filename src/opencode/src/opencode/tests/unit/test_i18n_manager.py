"""Tests for I18n Manager module."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from opencode.i18n.manager import (
    I18nManager,
    Language,
    SUPPORTED_LANGUAGES,
    get_i18n,
    set_language,
    t,
    _,
)


class TestLanguage:
    """Tests for Language dataclass."""

    def test_language_creation(self):
        """Test creating a language."""
        lang = Language("en", "English", "English")
        
        assert lang.code == "en"
        assert lang.name == "English"
        assert lang.native_name == "English"
        assert lang.rtl is False

    def test_rtl_language(self):
        """Test creating an RTL language."""
        lang = Language("ar", "Arabic", "العربية", rtl=True)
        
        assert lang.code == "ar"
        assert lang.rtl is True


class TestSupportedLanguages:
    """Tests for supported languages."""

    def test_english_exists(self):
        """Test English is supported."""
        assert "en" in SUPPORTED_LANGUAGES
        assert SUPPORTED_LANGUAGES["en"].name == "English"

    def test_chinese_exists(self):
        """Test Chinese is supported."""
        assert "zh" in SUPPORTED_LANGUAGES
        assert SUPPORTED_LANGUAGES["zh"].native_name == "中文"

    def test_japanese_exists(self):
        """Test Japanese is supported."""
        assert "ja" in SUPPORTED_LANGUAGES
        assert SUPPORTED_LANGUAGES["ja"].native_name == "日本語"

    def test_spanish_exists(self):
        """Test Spanish is supported."""
        assert "es" in SUPPORTED_LANGUAGES
        assert SUPPORTED_LANGUAGES["es"].native_name == "Español"

    def test_arabic_is_rtl(self):
        """Test Arabic is marked as RTL."""
        assert "ar" in SUPPORTED_LANGUAGES
        assert SUPPORTED_LANGUAGES["ar"].rtl is True

    def test_all_languages_have_required_fields(self):
        """Test all languages have required fields."""
        for code, lang in SUPPORTED_LANGUAGES.items():
            assert lang.code == code
            assert lang.name
            assert lang.native_name


class TestI18nManager:
    """Tests for I18nManager class."""

    def test_init_default(self):
        """Test default initialization."""
        manager = I18nManager()
        
        assert manager.default_language == "en"
        assert manager.fallback_language == "en"
        assert manager.current_language in SUPPORTED_LANGUAGES

    def test_init_custom_language(self):
        """Test initialization with custom language."""
        manager = I18nManager(default_language="es")
        
        assert manager.default_language == "es"

    def test_init_custom_fallback(self):
        """Test initialization with custom fallback."""
        manager = I18nManager(fallback_language="en")
        
        assert manager.fallback_language == "en"

    def test_get_default_locale_dir(self):
        """Test default locale directory."""
        manager = I18nManager()
        
        locale_dir = manager._get_default_locale_dir()
        assert "locales" in str(locale_dir)

    def test_set_language_valid(self):
        """Test setting a valid language."""
        manager = I18nManager(default_language="en")
        
        result = manager.set_language("es")
        
        assert result is True
        assert manager.current_language == "es"

    def test_set_language_invalid(self):
        """Test setting an invalid language."""
        manager = I18nManager()
        
        result = manager.set_language("invalid_lang")
        
        assert result is False

    def test_current_language_info(self):
        """Test getting current language info."""
        manager = I18nManager(default_language="en")
        
        info = manager.current_language_info
        
        assert isinstance(info, Language)
        assert info.code == manager.current_language

    def test_get_supported_languages(self):
        """Test getting supported languages list."""
        manager = I18nManager()
        
        languages = manager.get_supported_languages()
        
        assert len(languages) == len(SUPPORTED_LANGUAGES)
        assert all(isinstance(lang, Language) for lang in languages)

    def test_t_simple_key(self):
        """Test translating a simple key."""
        manager = I18nManager(default_language="en")
        
        translation = manager.t("app.name")
        
        assert translation == "OpenCode"

    def test_t_nested_key(self):
        """Test translating a nested key."""
        manager = I18nManager(default_language="en")
        
        translation = manager.t("cli.help")
        
        assert "help" in translation.lower() or translation == "Show help message"

    def test_t_missing_key(self):
        """Test translating a missing key returns the key."""
        manager = I18nManager()
        
        translation = manager.t("nonexistent.key")
        
        assert translation == "nonexistent.key"

    def test_t_with_default(self):
        """Test translating with a default value."""
        manager = I18nManager()
        
        translation = manager.t("missing.key", default="Default Value")
        
        assert translation == "Default Value"

    def test_t_with_interpolation(self):
        """Test translating with variable interpolation."""
        manager = I18nManager(default_language="en")
        
        translation = manager.t("provider.connected", provider="OpenAI")
        
        assert "OpenAI" in translation

    def test_t_with_missing_interpolation_var(self):
        """Test translating with missing interpolation variable."""
        manager = I18nManager(default_language="en")
        
        # Should not raise, just log warning
        translation = manager.t("provider.connected")
        
        assert translation is not None

    def test_pluralize_singular(self):
        """Test pluralization with singular count."""
        manager = I18nManager(default_language="en")
        
        translation = manager.pluralize("session.new", count=1)
        
        assert translation is not None

    def test_pluralize_plural(self):
        """Test pluralization with plural count."""
        manager = I18nManager(default_language="en")
        
        translation = manager.pluralize("session.new", count=5)
        
        assert translation is not None

    def test_reload(self):
        """Test reloading translations."""
        manager = I18nManager(default_language="en")
        
        # Load some translations
        manager.t("app.name")
        
        # Reload
        manager.reload()
        
        # Should still work
        translation = manager.t("app.name")
        assert translation == "OpenCode"

    def test_detect_system_language_from_env(self):
        """Test detecting language from environment."""
        with patch.dict("os.environ", {"LANG": "es_ES.UTF-8"}):
            manager = I18nManager()
            # The detection happens during init, but we can test the method
            detected = manager._detect_system_language()
            assert detected in SUPPORTED_LANGUAGES or detected == "en"

    def test_detect_system_language_opencode_lang(self):
        """Test detecting language from OPENCODE_LANG."""
        with patch.dict("os.environ", {"OPENCODE_LANG": "ja"}, clear=False):
            # Remove other lang vars if present
            manager = I18nManager()
            detected = manager._detect_system_language()
            assert detected == "ja"

    def test_load_language_already_loaded(self):
        """Test loading an already loaded language."""
        manager = I18nManager(default_language="en")
        
        # English is loaded by default
        result = manager._load_language("en")
        
        assert result is True

    def test_get_translation_missing_language(self):
        """Test getting translation from unloaded language."""
        manager = I18nManager()
        
        translation = manager._get_translation("xx", "app.name")
        
        assert translation is None

    def test_get_translation_missing_key(self):
        """Test getting missing translation."""
        manager = I18nManager(default_language="en")
        
        translation = manager._get_translation("en", "nonexistent.key")
        
        assert translation is None

    def test_deep_merge(self):
        """Test deep merge functionality."""
        manager = I18nManager()
        
        base = {"a": 1, "b": {"c": 2, "d": 3}}
        override = {"b": {"c": 10}}
        
        result = manager._deep_merge(base, override)
        
        assert result["a"] == 1
        assert result["b"]["c"] == 10
        assert result["b"]["d"] == 3

    def test_get_embedded_translations_english(self):
        """Test getting embedded English translations."""
        manager = I18nManager()
        
        translations = manager._get_embedded_translations("en")
        
        assert "app" in translations
        assert translations["app"]["name"] == "OpenCode"

    def test_get_embedded_translations_chinese(self):
        """Test getting embedded Chinese translations."""
        manager = I18nManager()
        
        translations = manager._get_embedded_translations("zh")
        
        assert "app" in translations

    def test_get_embedded_translations_unknown(self):
        """Test getting embedded translations for unknown language."""
        manager = I18nManager()
        
        translations = manager._get_embedded_translations("unknown")
        
        # Should return empty dict or base translations
        assert isinstance(translations, dict)


class TestGlobalFunctions:
    """Tests for global i18n functions."""

    def test_get_i18n_singleton(self):
        """Test get_i18n returns singleton."""
        # Reset the global instance
        import opencode.i18n.manager as i18n_module
        i18n_module._i18n_manager = None
        
        manager1 = get_i18n()
        manager2 = get_i18n()
        
        assert manager1 is manager2

    def test_set_language_global(self):
        """Test global set_language function."""
        # Reset the global instance
        import opencode.i18n.manager as i18n_module
        i18n_module._i18n_manager = None
        
        result = set_language("es")
        
        assert result is True
        assert get_i18n().current_language == "es"

    def test_t_global(self):
        """Test global t function."""
        # Reset the global instance
        import opencode.i18n.manager as i18n_module
        i18n_module._i18n_manager = None
        
        translation = t("app.name")
        
        assert translation == "OpenCode"

    def test_shorthand_underscore(self):
        """Test shorthand _ function."""
        # Reset the global instance
        import opencode.i18n.manager as i18n_module
        i18n_module._i18n_manager = None
        
        translation = _("app.name")
        
        assert translation == "OpenCode"


class TestI18nManagerWithLocaleDir:
    """Tests for I18nManager with custom locale directory."""

    def test_custom_locale_dir(self, tmp_path):
        """Test with custom locale directory."""
        # Create a custom locale file
        locale_dir = tmp_path / "locales"
        locale_dir.mkdir()
        
        locale_file = locale_dir / "test.json"
        locale_file.write_text('{"greeting": "Hello"}')
        
        manager = I18nManager(locale_dir=locale_dir, default_language="test")
        
        # Should load from custom directory
        assert manager.locale_dir == locale_dir

    def test_missing_locale_file(self, tmp_path):
        """Test with missing locale file."""
        locale_dir = tmp_path / "locales"
        locale_dir.mkdir()
        
        # No file for this language
        manager = I18nManager(locale_dir=locale_dir, default_language="missing")
        
        # Should fall back to embedded translations
        assert manager._translations is not None
