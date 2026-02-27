"""
Base class that all AI providers inherit from.
This ensures every provider has the same interface.
"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseProvider(ABC):
    """Every provider must implement these methods."""

    # ── Free model catalog ─────────────────────────────────────────────
    # List of dicts with keys: "id", "name", "description"
    FREE_MODELS: list[dict] = []

    # ── Free tier limits ───────────────────────────────────────────────
    # Describes what the free tier allows and when limits reset.
    # Keys explained:
    #   tier_name         — display name for the plan (e.g. "Free Tier")
    #   signup_url        — where to get an API key
    #   dashboard_url     — where to check real-time usage/quotas
    #   reset_schedule    — human description of when limits reset
    #   reset_type        — "daily" | "monthly" | "rolling_minute" | "rolling_day"
    #   global_limits     — limits that apply across all models
    #   model_limits      — per-model overrides (keyed by model id)
    #   notes             — list of extra tips / caveats
    FREE_TIER_LIMITS: dict = {}

    def __init__(self, api_key: str, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or self.default_model

    # ------------------------------------------------------------------
    # Abstract — subclasses must implement
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def default_model(self) -> str:
        """The default model to use if none is specified."""
        ...

    @abstractmethod
    def chat(self, prompt: str, system: Optional[str] = None) -> str:
        """
        Send a prompt and get a text response back.

        Args:
            prompt:  The user's message.
            system:  An optional system instruction.

        Returns:
            The AI's reply as a plain string.
        """
        ...

    # ------------------------------------------------------------------
    # Model management
    # ------------------------------------------------------------------

    @classmethod
    def list_free_models(cls) -> list[dict]:
        """Return the list of known free models for this provider."""
        return cls.FREE_MODELS

    def set_model(self, model_id: str) -> None:
        """Switch to a different model by its ID string."""
        valid_ids = [m["id"] for m in self.FREE_MODELS]
        if valid_ids and model_id not in valid_ids:
            print(f"⚠️  '{model_id}' is not in the known free-model list, but setting it anyway.")
        self.model = model_id
        print(f"🔀  Model switched to: {model_id}")

    def current_model_info(self) -> Optional[dict]:
        """Return the FREE_MODELS entry for the currently active model, or None."""
        for m in self.FREE_MODELS:
            if m["id"] == self.model:
                return m
        return None

    # ------------------------------------------------------------------
    # Limits
    # ------------------------------------------------------------------

    @classmethod
    def get_limits(cls) -> dict:
        """
        Return the free-tier limits for this provider.

        Returns a dict (see FREE_TIER_LIMITS definition above).
        Returns an empty dict if no limit data is available.
        """
        return cls.FREE_TIER_LIMITS

    def get_model_limits(self, model_id: Optional[str] = None) -> dict:
        """
        Return limits for a specific model (falls back to global limits).

        Args:
            model_id: model to look up; uses self.model if not given.

        Returns a dict with keys like requests_per_minute, tokens_per_day, etc.
        None values mean "not publicly documented / assumed unlimited".
        """
        target = model_id or self.model
        limits = self.FREE_TIER_LIMITS

        # Start with global limits as the base
        result = dict(limits.get("global_limits", {}))

        # Override with model-specific limits if they exist
        model_overrides = limits.get("model_limits", {}).get(target, {})
        result.update(model_overrides)

        return result

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model!r})"
