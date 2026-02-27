"""Internationalization manager for OpenCode.

Supports 17+ languages with automatic detection, pluralization,
and variable interpolation.
"""

from __future__ import annotations

import json
import locale
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class Language:
    """Language configuration."""
    code: str
    name: str
    native_name: str
    rtl: bool = False  # Right-to-left language


# Supported languages
SUPPORTED_LANGUAGES: dict[str, Language] = {
    "en": Language("en", "English", "English"),
    "zh": Language("zh", "Chinese", "中文"),
    "zh-TW": Language("zh-TW", "Chinese (Traditional)", "繁體中文"),
    "ja": Language("ja", "Japanese", "日本語"),
    "ko": Language("ko", "Korean", "한국어"),
    "es": Language("es", "Spanish", "Español"),
    "fr": Language("fr", "French", "Français"),
    "de": Language("de", "German", "Deutsch"),
    "it": Language("it", "Italian", "Italiano"),
    "pt": Language("pt", "Portuguese", "Português"),
    "pt-BR": Language("pt-BR", "Portuguese (Brazil)", "Português (Brasil)"),
    "ru": Language("ru", "Russian", "Русский"),
    "ar": Language("ar", "Arabic", "العربية", rtl=True),
    "hi": Language("hi", "Hindi", "हिन्दी"),
    "tr": Language("tr", "Turkish", "Türkçe"),
    "vi": Language("vi", "Vietnamese", "Tiếng Việt"),
    "th": Language("th", "Thai", "ไทย"),
    "pl": Language("pl", "Polish", "Polski"),
    "nl": Language("nl", "Dutch", "Nederlands"),
    "uk": Language("uk", "Ukrainian", "Українська"),
}


class I18nManager:
    """Manages internationalization for OpenCode.
    
    Features:
    - 17+ supported languages
    - Automatic language detection from system
    - Pluralization support
    - Variable interpolation
    - Fallback to English for missing translations
    - Hot-reload of translations
    
    Usage:
        i18n = I18nManager()
        i18n.set_language("es")
        msg = i18n.t("welcome.message", name="User")
    """
    
    def __init__(
        self,
        locale_dir: Optional[Path] = None,
        default_language: str = "en",
        fallback_language: str = "en",
    ):
        """Initialize the i18n manager.
        
        Args:
            locale_dir: Directory containing translation files
            default_language: Default language to use
            fallback_language: Fallback language for missing translations
        """
        self.locale_dir = locale_dir or self._get_default_locale_dir()
        self.default_language = default_language
        self.fallback_language = fallback_language
        self._current_language = default_language
        self._translations: dict[str, dict[str, Any]] = {}
        self._loaded_languages: set[str] = set()
        
        # Auto-detect system language
        if default_language == "en":
            detected = self._detect_system_language()
            if detected in SUPPORTED_LANGUAGES:
                self._current_language = detected
        
        # Load default language
        self._load_language(self._current_language)
        if self._current_language != self.fallback_language:
            self._load_language(self.fallback_language)
    
    def _get_default_locale_dir(self) -> Path:
        """Get the default locale directory."""
        return Path(__file__).parent / "locales"
    
    def _detect_system_language(self) -> str:
        """Detect the system language.
        
        Returns:
            Language code (e.g., 'en', 'es', 'zh')
        """
        # Check environment variables first
        for env_var in ("OPENCODE_LANG", "LANG", "LANGUAGE"):
            lang_env = os.environ.get(env_var)
            if lang_env:
                # Parse language code (e.g., 'en_US.UTF-8' -> 'en')
                lang_code = lang_env.split(".")[0].split("_")[0]
                if lang_code in SUPPORTED_LANGUAGES:
                    return lang_code
                # Check for full locale (e.g., 'zh_TW' -> 'zh-TW')
                if "_" in lang_env:
                    parts = lang_env.split(".")[0].split("_")
                    if len(parts) >= 2:
                        full_code = f"{parts[0]}-{parts[1]}"
                        if full_code in SUPPORTED_LANGUAGES:
                            return full_code
        
        # Try system locale
        try:
            sys_locale = locale.getdefaultlocale()[0]
            if sys_locale:
                lang_code = sys_locale.split("_")[0]
                if lang_code in SUPPORTED_LANGUAGES:
                    return lang_code
                # Check full locale
                if "_" in sys_locale:
                    parts = sys_locale.split("_")
                    full_code = f"{parts[0]}-{parts[1]}"
                    if full_code in SUPPORTED_LANGUAGES:
                        return full_code
        except Exception:
            pass
        
        return self.default_language
    
    def _load_language(self, language_code: str) -> bool:
        """Load translations for a language.
        
        Args:
            language_code: Language code to load
            
        Returns:
            True if loaded successfully, False otherwise
        """
        if language_code in self._loaded_languages:
            return True
        
        # Try to load from JSON file
        locale_file = self.locale_dir / f"{language_code}.json"
        
        if locale_file.exists():
            try:
                with open(locale_file, "r", encoding="utf-8") as f:
                    self._translations[language_code] = json.load(f)
                self._loaded_languages.add(language_code)
                logger.debug(f"Loaded translations for {language_code}")
                return True
            except Exception as e:
                logger.warning(f"Failed to load translations for {language_code}: {e}")
        
        # Fall back to embedded translations
        self._translations[language_code] = self._get_embedded_translations(language_code)
        self._loaded_languages.add(language_code)
        return True
    
    def _get_embedded_translations(self, language_code: str) -> dict[str, Any]:
        """Get embedded translations for a language.
        
        These are fallback translations embedded in the code.
        """
        # English is the base
        base_translations = {
            "app": {
                "name": "OpenCode",
                "version": "1.0.0",
                "description": "AI-powered coding assistant",
            },
            "cli": {
                "help": "Show help message",
                "version": "Show version",
                "config": "Configuration options",
                "session": "Session management",
            },
            "session": {
                "new": "New session created",
                "saved": "Session saved",
                "loaded": "Session loaded",
                "not_found": "Session not found",
                "list": "Sessions:",
            },
            "provider": {
                "connected": "Connected to {provider}",
                "error": "Error connecting to {provider}: {error}",
                "not_configured": "Provider {provider} not configured",
            },
            "tool": {
                "executing": "Executing {tool}...",
                "success": "{tool} completed successfully",
                "error": "{tool} failed: {error}",
                "not_found": "Tool not found: {tool}",
            },
            "tui": {
                "welcome": "Welcome to OpenCode!",
                "input_placeholder": "Type your message...",
                "thinking": "Thinking...",
                "processing": "Processing...",
            },
            "error": {
                "generic": "An error occurred",
                "not_implemented": "Feature not implemented",
                "invalid_input": "Invalid input: {input}",
                "permission_denied": "Permission denied",
            },
            "confirm": {
                "yes": "Yes",
                "no": "No",
                "cancel": "Cancel",
                "continue": "Continue",
                "abort": "Abort",
            },
            "file": {
                "read": "Reading file: {path}",
                "write": "Writing file: {path}",
                "not_found": "File not found: {path}",
                "permission_denied": "Permission denied: {path}",
            },
            "git": {
                "status": "Git status",
                "commit": "Commit: {message}",
                "branch": "Branch: {branch}",
                "no_changes": "No changes to commit",
            },
            "lsp": {
                "starting": "Starting LSP server for {language}",
                "ready": "LSP server ready",
                "error": "LSP error: {error}",
            },
            "mcp": {
                "connected": "MCP server connected",
                "disconnected": "MCP server disconnected",
                "tool_call": "Calling MCP tool: {tool}",
            },
        }
        
        if language_code == "en":
            return base_translations
        
        # Add translations for other languages
        translations_map: dict[str, dict[str, Any]] = {
            "zh": {
                "app": {
                    "name": "OpenCode",
                    "version": "1.0.0",
                    "description": "AI驱动的编程助手",
                },
                "cli": {
                    "help": "显示帮助信息",
                    "version": "显示版本",
                    "config": "配置选项",
                    "session": "会话管理",
                },
                "session": {
                    "new": "已创建新会话",
                    "saved": "会话已保存",
                    "loaded": "会话已加载",
                    "not_found": "未找到会话",
                    "list": "会话列表：",
                },
                "tui": {
                    "welcome": "欢迎使用 OpenCode！",
                    "input_placeholder": "输入您的消息...",
                    "thinking": "思考中...",
                    "processing": "处理中...",
                },
                "error": {
                    "generic": "发生错误",
                    "not_implemented": "功能未实现",
                    "invalid_input": "无效输入：{input}",
                    "permission_denied": "权限被拒绝",
                },
                "confirm": {
                    "yes": "是",
                    "no": "否",
                    "cancel": "取消",
                    "continue": "继续",
                    "abort": "中止",
                },
            },
            "es": {
                "app": {
                    "name": "OpenCode",
                    "description": "Asistente de programación con IA",
                },
                "tui": {
                    "welcome": "¡Bienvenido a OpenCode!",
                    "input_placeholder": "Escribe tu mensaje...",
                    "thinking": "Pensando...",
                },
                "confirm": {
                    "yes": "Sí",
                    "no": "No",
                    "cancel": "Cancelar",
                },
            },
            "fr": {
                "app": {
                    "name": "OpenCode",
                    "description": "Assistant de programmation IA",
                },
                "tui": {
                    "welcome": "Bienvenue dans OpenCode !",
                    "input_placeholder": "Tapez votre message...",
                    "thinking": "Réflexion...",
                },
                "confirm": {
                    "yes": "Oui",
                    "no": "Non",
                    "cancel": "Annuler",
                },
            },
            "de": {
                "app": {
                    "name": "OpenCode",
                    "description": "KI-gestützter Programmierassistent",
                },
                "tui": {
                    "welcome": "Willkommen bei OpenCode!",
                    "input_placeholder": "Geben Sie Ihre Nachricht ein...",
                    "thinking": "Denken...",
                },
                "confirm": {
                    "yes": "Ja",
                    "no": "Nein",
                    "cancel": "Abbrechen",
                },
            },
            "ja": {
                "app": {
                    "name": "OpenCode",
                    "description": "AI搭載プログラミングアシスタント",
                },
                "tui": {
                    "welcome": "OpenCodeへようこそ！",
                    "input_placeholder": "メッセージを入力...",
                    "thinking": "考え中...",
                },
                "confirm": {
                    "yes": "はい",
                    "no": "いいえ",
                    "cancel": "キャンセル",
                },
            },
            "ko": {
                "app": {
                    "name": "OpenCode",
                    "description": "AI 기반 프로그래밍 도우미",
                },
                "tui": {
                    "welcome": "OpenCode에 오신 것을 환영합니다!",
                    "input_placeholder": "메시지를 입력하세요...",
                    "thinking": "생각 중...",
                },
                "confirm": {
                    "yes": "예",
                    "no": "아니오",
                    "cancel": "취소",
                },
            },
            "pt": {
                "app": {
                    "name": "OpenCode",
                    "description": "Assistente de programação com IA",
                },
                "tui": {
                    "welcome": "Bem-vindo ao OpenCode!",
                    "input_placeholder": "Digite sua mensagem...",
                    "thinking": "Pensando...",
                },
                "confirm": {
                    "yes": "Sim",
                    "no": "Não",
                    "cancel": "Cancelar",
                },
            },
            "ru": {
                "app": {
                    "name": "OpenCode",
                    "description": "ИИ-помощник для программирования",
                },
                "tui": {
                    "welcome": "Добро пожаловать в OpenCode!",
                    "input_placeholder": "Введите сообщение...",
                    "thinking": "Думаю...",
                },
                "confirm": {
                    "yes": "Да",
                    "no": "Нет",
                    "cancel": "Отмена",
                },
            },
            "ar": {
                "app": {
                    "name": "OpenCode",
                    "description": "مساعد برمجة بالذكاء الاصطناعي",
                },
                "tui": {
                    "welcome": "مرحباً بك في OpenCode!",
                    "input_placeholder": "اكتب رسالتك...",
                    "thinking": "جاري التفكير...",
                },
                "confirm": {
                    "yes": "نعم",
                    "no": "لا",
                    "cancel": "إلغاء",
                },
            },
            "hi": {
                "app": {
                    "name": "OpenCode",
                    "description": "AI-संचालित प्रोग्रामिंग सहायक",
                },
                "tui": {
                    "welcome": "OpenCode में आपका स्वागत है!",
                    "input_placeholder": "अपना संदेश टाइप करें...",
                    "thinking": "सोच रहा हूं...",
                },
                "confirm": {
                    "yes": "हाँ",
                    "no": "नहीं",
                    "cancel": "रद्द करें",
                },
            },
            "tr": {
                "app": {
                    "name": "OpenCode",
                    "description": "AI destekli programlama asistanı",
                },
                "tui": {
                    "welcome": "OpenCode'a hoş geldiniz!",
                    "input_placeholder": "Mesajınızı yazın...",
                    "thinking": "Düşünüyorum...",
                },
                "confirm": {
                    "yes": "Evet",
                    "no": "Hayır",
                    "cancel": "İptal",
                },
            },
            "vi": {
                "app": {
                    "name": "OpenCode",
                    "description": "Trợ lý lập trình AI",
                },
                "tui": {
                    "welcome": "Chào mừng đến với OpenCode!",
                    "input_placeholder": "Nhập tin nhắn của bạn...",
                    "thinking": "Đang suy nghĩ...",
                },
                "confirm": {
                    "yes": "Có",
                    "no": "Không",
                    "cancel": "Hủy",
                },
            },
            "th": {
                "app": {
                    "name": "OpenCode",
                    "description": "ผู้ช่วยเขียนโปรแกรม AI",
                },
                "tui": {
                    "welcome": "ยินดีต้อนรับสู่ OpenCode!",
                    "input_placeholder": "พิมพ์ข้อความของคุณ...",
                    "thinking": "กำลังคิด...",
                },
                "confirm": {
                    "yes": "ใช่",
                    "no": "ไม่",
                    "cancel": "ยกเลิก",
                },
            },
            "pl": {
                "app": {
                    "name": "OpenCode",
                    "description": "Asystent programowania AI",
                },
                "tui": {
                    "welcome": "Witamy w OpenCode!",
                    "input_placeholder": "Wpisz wiadomość...",
                    "thinking": "Myślę...",
                },
                "confirm": {
                    "yes": "Tak",
                    "no": "Nie",
                    "cancel": "Anuluj",
                },
            },
            "nl": {
                "app": {
                    "name": "OpenCode",
                    "description": "AI-programmeerassistent",
                },
                "tui": {
                    "welcome": "Welkom bij OpenCode!",
                    "input_placeholder": "Typ uw bericht...",
                    "thinking": "Denken...",
                },
                "confirm": {
                    "yes": "Ja",
                    "no": "Nee",
                    "cancel": "Annuleren",
                },
            },
            "uk": {
                "app": {
                    "name": "OpenCode",
                    "description": "ІІ-помічник для програмування",
                },
                "tui": {
                    "welcome": "Ласкаво просимо до OpenCode!",
                    "input_placeholder": "Введіть повідомлення...",
                    "thinking": "Думаю...",
                },
                "confirm": {
                    "yes": "Так",
                    "no": "Ні",
                    "cancel": "Скасувати",
                },
            },
        }
        
        # Merge with base translations
        result = dict(base_translations)
        if language_code in translations_map:
            result = self._deep_merge(result, translations_map[language_code])
        
        return result
    
    def _deep_merge(
        self,
        base: dict[str, Any],
        override: dict[str, Any],
    ) -> dict[str, Any]:
        """Deep merge two dictionaries.
        
        Args:
            base: Base dictionary
            override: Override dictionary
            
        Returns:
            Merged dictionary
        """
        result = dict(base)
        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    @property
    def current_language(self) -> str:
        """Get the current language code."""
        return self._current_language
    
    @property
    def current_language_info(self) -> Language:
        """Get the current language information."""
        return SUPPORTED_LANGUAGES.get(
            self._current_language,
            SUPPORTED_LANGUAGES["en"],
        )
    
    def set_language(self, language_code: str) -> bool:
        """Set the current language.
        
        Args:
            language_code: Language code to set
            
        Returns:
            True if language was set successfully
        """
        if language_code not in SUPPORTED_LANGUAGES:
            logger.warning(f"Unsupported language: {language_code}")
            return False
        
        self._current_language = language_code
        self._load_language(language_code)
        logger.info(f"Language set to {language_code}")
        return True
    
    def get_supported_languages(self) -> list[Language]:
        """Get list of supported languages."""
        return list(SUPPORTED_LANGUAGES.values())
    
    def t(
        self,
        key: str,
        default: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """Translate a key to the current language.
        
        Args:
            key: Translation key (dot-separated, e.g., "app.name")
            default: Default value if key not found
            **kwargs: Variables for interpolation
            
        Returns:
            Translated string with variables interpolated
        """
        # Try current language first
        translation = self._get_translation(self._current_language, key)
        
        # Fall back to fallback language
        if translation is None and self._current_language != self.fallback_language:
            translation = self._get_translation(self.fallback_language, key)
        
        # Use default or key
        if translation is None:
            translation = default if default is not None else key
        
        # Interpolate variables
        if kwargs:
            try:
                translation = translation.format(**kwargs)
            except KeyError as e:
                logger.warning(f"Missing interpolation variable: {e}")
        
        return translation
    
    def _get_translation(self, language_code: str, key: str) -> Optional[str]:
        """Get a translation from a specific language.
        
        Args:
            language_code: Language code
            key: Translation key (dot-separated)
            
        Returns:
            Translation string or None if not found
        """
        if language_code not in self._translations:
            return None
        
        # Navigate the translation tree
        parts = key.split(".")
        current: Any = self._translations[language_code]
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        if isinstance(current, str):
            return current
        return None
    
    def pluralize(
        self,
        key: str,
        count: int,
        **kwargs: Any,
    ) -> str:
        """Translate with pluralization.
        
        Args:
            key: Translation key
            count: Count for pluralization
            **kwargs: Variables for interpolation
            
        Returns:
            Translated string with correct plural form
        """
        # Try to get plural forms
        plural_key = f"{key}_plural" if count != 1 else key
        translation = self.t(plural_key, default=None, count=count, **kwargs)
        
        if translation == plural_key:
            # No plural form found, try with count variable
            translation = self.t(key, default=None, count=count, **kwargs)
        
        return translation
    
    def reload(self) -> None:
        """Reload all translations from disk."""
        self._loaded_languages.clear()
        self._translations.clear()
        self._load_language(self._current_language)
        if self._current_language != self.fallback_language:
            self._load_language(self.fallback_language)
        logger.info("Translations reloaded")


# Global i18n manager instance
_i18n_manager: Optional[I18nManager] = None


def get_i18n() -> I18nManager:
    """Get the global i18n manager instance."""
    global _i18n_manager
    if _i18n_manager is None:
        _i18n_manager = I18nManager()
    return _i18n_manager


def set_language(language_code: str) -> bool:
    """Set the global language."""
    return get_i18n().set_language(language_code)


def t(key: str, default: Optional[str] = None, **kwargs: Any) -> str:
    """Translate a key using the global i18n manager."""
    return get_i18n().t(key, default=default, **kwargs)


def _(key: str, default: Optional[str] = None, **kwargs: Any) -> str:
    """Shorthand for t() - translate a key."""
    return t(key, default=default, **kwargs)
