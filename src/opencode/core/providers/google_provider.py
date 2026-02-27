"""
Google AI Studio provider — uses the Gemini family of models.
Get a free API key at: https://aistudio.google.com/app/apikey
"""

from typing import Optional
from .base import BaseProvider


class GoogleAIProvider(BaseProvider):
    """Connects to Google AI Studio (Gemini models)."""

    FREE_MODELS = [
        {"id": "gemini-1.5-flash",      "name": "Gemini 1.5 Flash",      "description": "⚡ Fast & efficient. Great for everyday tasks. 1M token context."},
        {"id": "gemini-1.5-flash-8b",   "name": "Gemini 1.5 Flash 8B",   "description": "⚡⚡ Smallest / fastest Gemini. High volume, simple tasks."},
        {"id": "gemini-1.5-pro",        "name": "Gemini 1.5 Pro",        "description": "🧠 Most capable free Gemini. Complex reasoning, 2M token context."},
        {"id": "gemini-2.0-flash-lite", "name": "Gemini 2.0 Flash Lite", "description": "🆕 Newest lightweight model. Cost-efficient next-gen performance."},
        {"id": "gemini-2.0-flash",      "name": "Gemini 2.0 Flash",      "description": "🆕 Next-gen speed + quality. Multimodal with tool use support."},
    ]

    FREE_TIER_LIMITS = {
        "tier_name": "Free Tier (AI Studio)",
        "signup_url": "https://aistudio.google.com/app/apikey",
        "dashboard_url": "https://aistudio.google.com/",
        "reset_schedule": "Per-minute limits are rolling windows. Daily limits reset at midnight Pacific Time.",
        "reset_type": "daily",
        "global_limits": {
            "credit_card_required": False,
        },
        "model_limits": {
            "gemini-1.5-flash": {
                "requests_per_minute": 15,
                "requests_per_day": 1_500,
                "tokens_per_minute": 1_000_000,
                "tokens_per_day": None,
            },
            "gemini-1.5-flash-8b": {
                "requests_per_minute": 15,
                "requests_per_day": 1_500,
                "tokens_per_minute": 1_000_000,
                "tokens_per_day": None,
            },
            "gemini-1.5-pro": {
                "requests_per_minute": 2,
                "requests_per_day": 50,
                "tokens_per_minute": 32_000,
                "tokens_per_day": None,
            },
            "gemini-2.0-flash-lite": {
                "requests_per_minute": 30,
                "requests_per_day": 1_500,
                "tokens_per_minute": 1_000_000,
                "tokens_per_day": None,
            },
            "gemini-2.0-flash": {
                "requests_per_minute": 15,
                "requests_per_day": 1_500,
                "tokens_per_minute": 1_000_000,
                "tokens_per_day": None,
            },
        },
        "notes": [
            "No credit card required. Just sign in with Google.",
            "Gemini 1.5 Pro has a strict limit of only 50 requests/day on the free tier.",
            "Gemini 1.5 Flash is the best free option for most use cases.",
            "Usage data is available in Google AI Studio (no dedicated quota page).",
            "Live limits: https://ai.google.dev/gemini-api/docs/rate-limits",
        ],
    }

    @property
    def default_model(self) -> str:
        return "gemini-1.5-flash"

    def chat(self, prompt: str, system: Optional[str] = None) -> str:
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("Run:  pip install google-generativeai")

        genai.configure(api_key=self.api_key)
        kwargs = {}
        if system:
            kwargs["system_instruction"] = system
        model = genai.GenerativeModel(self.model, **kwargs)
        response = model.generate_content(prompt)
        return response.text or ""
