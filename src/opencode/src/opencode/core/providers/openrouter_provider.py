"""
OpenRouter provider — a gateway to many models, including free ones.
Get a free API key at: https://openrouter.ai/keys
"""

from typing import Optional
from .base import BaseProvider


class OpenRouterProvider(BaseProvider):
    """Connects to OpenRouter, which proxies many model providers."""

    FREE_MODELS = [
        {"id": "mistralai/mistral-7b-instruct:free",        "name": "Mistral 7B Instruct (free)",    "description": "🌟 Popular open model. Fast, well-rounded, great for chat."},
        {"id": "meta-llama/llama-3-8b-instruct:free",       "name": "Llama 3 8B Instruct (free)",    "description": "⚡ Meta's compact Llama 3. Fast and capable."},
        {"id": "meta-llama/llama-3.2-3b-instruct:free",     "name": "Llama 3.2 3B Instruct (free)",  "description": "⚡⚡ Tiny but surprisingly capable. Ultra-fast responses."},
        {"id": "google/gemma-2-9b-it:free",                 "name": "Gemma 2 9B (free)",             "description": "🔷 Google's open Gemma 2. Instruction-tuned, solid quality."},
        {"id": "microsoft/phi-3-mini-128k-instruct:free",   "name": "Phi-3 Mini 128K (free)",        "description": "🔬 Microsoft's small but punchy model. 128K context."},
        {"id": "qwen/qwen-2-7b-instruct:free",              "name": "Qwen 2 7B (free)",              "description": "🀄 Alibaba's multilingual model. Strong at coding & reasoning."},
        {"id": "openchat/openchat-7b:free",                 "name": "OpenChat 7B (free)",            "description": "💬 Fine-tuned for conversation. Friendly and responsive."},
        {"id": "nousresearch/nous-capybara-7b:free",        "name": "Nous Capybara 7B (free)",       "description": "🦦 Community fine-tune. Good at instruction following."},
    ]

    FREE_TIER_LIMITS = {
        "tier_name": "Free Tier",
        "signup_url": "https://openrouter.ai/keys",
        "dashboard_url": "https://openrouter.ai/activity",
        "reset_schedule": "Rate limits are rolling per-minute windows. Free credits do not expire.",
        "reset_type": "rolling_minute",
        "global_limits": {
            "requests_per_minute": 20,
            "requests_per_day": 200,
            "tokens_per_minute": None,
            "tokens_per_day": None,
            "credit_card_required": False,
            "new_user_credits_usd": 1.00,
        },
        "model_limits": {},   # Free (:free) models share the global pool
        "notes": [
            "New accounts get $1 in free credits to try paid models.",
            "Models with ':free' suffix are permanently free — no credits consumed.",
            "Free models may have higher latency (lower priority queue).",
            "Daily limit of 200 requests applies to free models.",
            "Live usage: https://openrouter.ai/activity",
        ],
    }

    @property
    def default_model(self) -> str:
        return "mistralai/mistral-7b-instruct:free"

    def chat(self, prompt: str, system: Optional[str] = None) -> str:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Run:  pip install openai")

        client = OpenAI(api_key=self.api_key, base_url="https://openrouter.ai/api/v1")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(model=self.model, messages=messages)
        return response.choices[0].message.content or ""
