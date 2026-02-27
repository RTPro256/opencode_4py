"""
OpenAI provider — the original! Free tier gives limited credits to new accounts.
Get an API key at: https://platform.openai.com/api-keys
"""

from typing import Optional
from .base import BaseProvider


class OpenAIProvider(BaseProvider):
    """Connects to OpenAI's API."""

    FREE_MODELS = [
        {"id": "gpt-3.5-turbo",     "name": "GPT-3.5 Turbo",    "description": "⚡ Fast and affordable. Great for most everyday tasks."},
        {"id": "gpt-3.5-turbo-16k", "name": "GPT-3.5 Turbo 16K","description": "⚡ Same as above but with a larger 16K context window."},
        {"id": "gpt-4o-mini",       "name": "GPT-4o Mini",       "description": "🧠 Smarter than GPT-3.5 at a very low cost. Recommended upgrade."},
        {"id": "gpt-4o",            "name": "GPT-4o",            "description": "🚀 OpenAI's best model. Multimodal, fast, highly capable."},
    ]

    FREE_TIER_LIMITS = {
        "tier_name": "Free Trial Credits",
        "signup_url": "https://platform.openai.com/api-keys",
        "dashboard_url": "https://platform.openai.com/usage",
        "reset_schedule": "Free trial credits expire after 3 months. No recurring reset — it's a one-time grant.",
        "reset_type": "one_time",
        "global_limits": {
            "requests_per_minute": 3,        # tier 0 (free/trial)
            "requests_per_day": None,
            "tokens_per_minute": 40_000,
            "tokens_per_day": None,
            "credit_card_required": False,   # for trial; card needed to top up
            "free_trial_credit_usd": 5.00,
            "trial_expires_days": 90,
        },
        "model_limits": {
            "gpt-3.5-turbo": {
                "requests_per_minute": 3,
                "tokens_per_minute": 40_000,
                "tokens_per_day": 200_000,
            },
            "gpt-4o-mini": {
                "requests_per_minute": 3,
                "tokens_per_minute": 40_000,
                "tokens_per_day": 200_000,
            },
        },
        "notes": [
            "⚠️  Free tier is a one-time $5 credit for new accounts — it does NOT reset.",
            "Credits expire 90 days after account creation.",
            "After credits run out, you must add a payment method.",
            "Tier 0 (trial) has very low rate limits — only 3 RPM.",
            "Adding a payment method unlocks Tier 1 (much higher limits).",
            "Live usage & spend: https://platform.openai.com/usage",
        ],
    }

    @property
    def default_model(self) -> str:
        return "gpt-3.5-turbo"

    def chat(self, prompt: str, system: Optional[str] = None) -> str:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Run:  pip install openai")

        client = OpenAI(api_key=self.api_key)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(model=self.model, messages=messages)
        return response.choices[0].message.content
