"""
GitHub Models provider — free access to many models using your GitHub token.
Generate a token at: https://github.com/settings/tokens
"""

from typing import Optional
from .base import BaseProvider


class GitHubModelsProvider(BaseProvider):
    """Connects to GitHub Models, which exposes Azure-hosted AI models."""

    FREE_MODELS = [
        {"id": "gpt-4o-mini",                    "name": "GPT-4o Mini",            "description": "⚡ Fast and smart OpenAI model. Great everyday performance."},
        {"id": "gpt-4o",                         "name": "GPT-4o",                 "description": "🧠 OpenAI's flagship model. Top-tier reasoning and quality."},
        {"id": "meta-llama-3-8b-instruct",       "name": "Llama 3 8B Instruct",   "description": "⚡ Meta's compact open model. Fast and capable."},
        {"id": "meta-llama-3-70b-instruct",      "name": "Llama 3 70B Instruct",  "description": "🧠 Meta's large open model. Strong at complex reasoning."},
        {"id": "meta-llama-3.1-405b-instruct",   "name": "Llama 3.1 405B Instruct","description": "🚀 Massive open model. Near GPT-4 quality, 128K context."},
        {"id": "mistral-large",                  "name": "Mistral Large",          "description": "🌟 Mistral's flagship. Top-tier reasoning, multilingual."},
        {"id": "mistral-nemo",                   "name": "Mistral Nemo",           "description": "⚡ Compact Mistral. 128K context, efficient and accurate."},
        {"id": "phi-3-medium-128k-instruct",     "name": "Phi-3 Medium 128K",      "description": "🔬 Microsoft's mid-size Phi-3. Surprisingly capable for its size."},
        {"id": "phi-3-mini-128k-instruct",       "name": "Phi-3 Mini 128K",        "description": "🔬 Microsoft's tiny powerhouse. 128K context, very fast."},
        {"id": "ai21-jamba-1.5-large",           "name": "AI21 Jamba 1.5 Large",  "description": "🏗️ Hybrid SSM-Transformer. Fast with very long context."},
    ]

    FREE_TIER_LIMITS = {
        "tier_name": "Free (GitHub Personal Account)",
        "signup_url": "https://github.com/settings/tokens",
        "dashboard_url": "https://github.com/marketplace/models",
        "reset_schedule": "Rate limits are rolling per-minute and per-day windows.",
        "reset_type": "daily",
        "global_limits": {
            "requests_per_minute": 15,
            "requests_per_day": 150,
            "tokens_per_minute": None,
            "tokens_per_day": None,
            "credit_card_required": False,
        },
        "model_limits": {
            "gpt-4o": {
                "requests_per_minute": 8,
                "requests_per_day": 8,      # very limited for GPT-4o
                "tokens_per_minute": None,
                "tokens_per_day": None,
            },
            "gpt-4o-mini": {
                "requests_per_minute": 15,
                "requests_per_day": 150,
                "tokens_per_minute": None,
                "tokens_per_day": None,
            },
            "meta-llama-3.1-405b-instruct": {
                "requests_per_minute": 8,
                "requests_per_day": 8,
                "tokens_per_minute": None,
                "tokens_per_day": None,
            },
        },
        "notes": [
            "Only requires a GitHub personal access token (no special permissions needed).",
            "Limits are per GitHub account, not per token.",
            "Large/flagship models (GPT-4o, Llama 405B) have much tighter daily limits.",
            "GitHub Copilot subscribers get higher rate limits.",
            "Live limits: https://docs.github.com/en/github-models/prototyping-with-ai-models",
        ],
    }

    @property
    def default_model(self) -> str:
        return "gpt-4o-mini"

    def chat(self, prompt: str, system: Optional[str] = None) -> str:
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Run:  pip install openai")

        client = OpenAI(api_key=self.api_key, base_url="https://models.inference.ai.azure.com")
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(model=self.model, messages=messages)
        return response.choices[0].message.content or ""
