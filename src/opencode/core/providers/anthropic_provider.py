"""
Anthropic provider — the makers of Claude!
Get an API key at: https://console.anthropic.com/settings/keys

Free tier: New accounts receive a small credit to test the API.
After that, you need to deposit at least $5 to reach Tier 1.
(This is different from a Claude.ai subscription — the API is billed separately.)
"""

from typing import Optional
from .base import BaseProvider


class AnthropicProvider(BaseProvider):
    """Connects to Anthropic's Claude API."""

    FREE_MODELS = [
        {
            "id": "claude-haiku-4-5-20251001",
            "name": "Claude Haiku 4.5",
            "description": "⚡ Fastest & most affordable Claude. Great for high-volume tasks.",
        },
        {
            "id": "claude-sonnet-4-6",
            "name": "Claude Sonnet 4.6",
            "description": "⚖️  Best balance of speed and intelligence. Recommended default.",
        },
        {
            "id": "claude-opus-4-6",
            "name": "Claude Opus 4.6",
            "description": "🧠 Most powerful Claude. Deep reasoning, complex tasks.",
        },
    ]

    FREE_TIER_LIMITS = {
        "tier_name": "Free Trial / Tier 1",
        "signup_url": "https://console.anthropic.com/settings/keys",
        "dashboard_url": "https://console.anthropic.com/settings/usage",
        "reset_schedule": "Rate limits use rolling per-minute windows. Monthly spend limits reset on your billing date.",
        "reset_type": "rolling_minute",
        "global_limits": {
            "requests_per_minute": 5,          # Free/Tier 1 (Sonnet class)
            "requests_per_day": None,
            "tokens_per_minute": 20_000,       # ITPM at Tier 1
            "tokens_per_day": 300_000,         # tokens/day at Tier 1
            "credit_card_required": False,     # for the initial free credit
            "free_trial_credit_usd": None,    # small amount, not publicly specified
            "tier1_min_deposit_usd": 5.00,
            "tier1_monthly_spend_limit_usd": 100,
        },
        "model_limits": {
            "claude-haiku-4-5-20251001": {
                "requests_per_minute": 5,
                "tokens_per_minute": 25_000,
                "tokens_per_day": 300_000,
            },
            "claude-sonnet-4-6": {
                "requests_per_minute": 5,
                "tokens_per_minute": 20_000,
                "tokens_per_day": 300_000,
            },
            "claude-opus-4-6": {
                "requests_per_minute": 5,
                "tokens_per_minute": 10_000,
                "tokens_per_day": 300_000,
            },
        },
        "notes": [
            "⚠️  Free trial credits are small — exact amount not publicly specified.",
            "To continue after trial: deposit $5 minimum to unlock Tier 1.",
            "Tier 1 = 50 RPM, $100/month spend limit (pay-as-you-go).",
            "Claude Haiku is the cheapest model — great for experimenting on a budget.",
            "Haiku 4.5: ~$1 / 1M input tokens. Sonnet 4.6: ~$3 / 1M input tokens.",
            "This is the OFFICIAL Claude API — you are literally talking to Claude!",
            "Live usage & billing: https://console.anthropic.com/settings/usage",
        ],
    }

    @property
    def default_model(self) -> str:
        return "claude-haiku-4-5-20251001"   # cheapest for beginners

    def chat(self, prompt: str, system: Optional[str] = None) -> str:
        try:
            import anthropic
        except ImportError:
            raise ImportError("Run:  pip install anthropic")

        client = anthropic.Anthropic(api_key=self.api_key)

        kwargs = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system

        message = client.messages.create(**kwargs)
        return message.content[0].text
