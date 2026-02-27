"""
Groq provider — extremely fast inference, free tier available.
Get a free API key at: https://console.groq.com/keys
"""

from typing import Optional
from .base import BaseProvider


class GroqProvider(BaseProvider):
    """Connects to Groq's ultra-fast inference API."""

    FREE_MODELS = [
        {"id": "llama3-8b-8192",           "name": "Llama 3 8B",              "description": "⚡ Very fast. 8B parameters, 8K context. Great for quick tasks."},
        {"id": "llama3-70b-8192",           "name": "Llama 3 70B",             "description": "🧠 Smarter but still fast. 70B parameters, 8K context."},
        {"id": "llama-3.1-8b-instant",      "name": "Llama 3.1 8B Instant",   "description": "⚡ Updated Llama 3.1 — improved reasoning, 128K context."},
        {"id": "llama-3.1-70b-versatile",   "name": "Llama 3.1 70B Versatile","description": "🧠 Best quality on Groq free tier. 128K context window."},
        {"id": "mixtral-8x7b-32768",        "name": "Mixtral 8x7B",            "description": "🔀 Mixture-of-experts model. 32K context. Strong at reasoning."},
        {"id": "gemma2-9b-it",              "name": "Gemma 2 9B",              "description": "🔷 Google's open model. Instruction-tuned, efficient."},
        {"id": "gemma-7b-it",               "name": "Gemma 7B",               "description": "🔷 Google's compact open model. Fast and instruction-tuned."},
    ]

    FREE_TIER_LIMITS = {
        "tier_name": "Free Tier",
        "signup_url": "https://console.groq.com/keys",
        "dashboard_url": "https://console.groq.com/settings/limits",
        "reset_schedule": "Daily limits reset at midnight UTC. Per-minute limits are rolling windows.",
        "reset_type": "daily",
        "global_limits": {
            "requests_per_minute": None,      # varies by model
            "requests_per_day": None,         # varies by model
            "tokens_per_minute": None,        # varies by model
            "tokens_per_day": None,           # varies by model
            "credit_card_required": False,
        },
        "model_limits": {
            "llama3-8b-8192": {
                "requests_per_minute": 30,
                "requests_per_day": 14_400,
                "tokens_per_minute": 6_000,
                "tokens_per_day": None,
            },
            "llama3-70b-8192": {
                "requests_per_minute": 30,
                "requests_per_day": 14_400,
                "tokens_per_minute": 6_000,
                "tokens_per_day": None,
            },
            "llama-3.1-8b-instant": {
                "requests_per_minute": 30,
                "requests_per_day": 14_400,
                "tokens_per_minute": 20_000,
                "tokens_per_day": 500_000,
            },
            "llama-3.1-70b-versatile": {
                "requests_per_minute": 30,
                "requests_per_day": 14_400,
                "tokens_per_minute": 6_000,
                "tokens_per_day": 200_000,
            },
            "mixtral-8x7b-32768": {
                "requests_per_minute": 30,
                "requests_per_day": 14_400,
                "tokens_per_minute": 5_000,
                "tokens_per_day": None,
            },
            "gemma2-9b-it": {
                "requests_per_minute": 30,
                "requests_per_day": 14_400,
                "tokens_per_minute": 15_000,
                "tokens_per_day": 500_000,
            },
            "gemma-7b-it": {
                "requests_per_minute": 30,
                "requests_per_day": 14_400,
                "tokens_per_minute": 15_000,
                "tokens_per_day": 500_000,
            },
        },
        "notes": [
            "No credit card required to start.",
            "Per-model limits differ — check dashboard for up-to-date numbers.",
            "Groq is one of the most generous free tiers available.",
            "Live limits: https://console.groq.com/settings/limits",
        ],
    }

    @property
    def default_model(self) -> str:
        return "llama3-8b-8192"

    def chat(self, prompt: str, system: Optional[str] = None) -> str:
        try:
            from groq import Groq
        except ImportError:
            raise ImportError("Run:  pip install groq")

        client = Groq(api_key=self.api_key)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(model=self.model, messages=messages)
        return response.choices[0].message.content or ""
