"""
Hugging Face provider — free Inference API for thousands of community models.
Get a free token at: https://huggingface.co/settings/tokens
"""

from typing import Optional
from .base import BaseProvider


class HuggingFaceProvider(BaseProvider):
    """Connects to Hugging Face's free Inference API."""

    FREE_MODELS = [
        {"id": "mistralai/Mistral-7B-Instruct-v0.3",  "name": "Mistral 7B Instruct v0.3", "description": "🌟 Reliable, well-rounded open model. Great all-purpose choice."},
        {"id": "HuggingFaceH4/zephyr-7b-beta",        "name": "Zephyr 7B Beta",            "description": "💬 Fine-tuned for helpful chat. Friendly and accurate."},
        {"id": "tiiuae/falcon-7b-instruct",            "name": "Falcon 7B Instruct",        "description": "🦅 Instruction-following model from TII. Fast inference."},
        {"id": "google/flan-t5-xxl",                  "name": "Flan-T5 XXL",               "description": "📚 Google's encoder-decoder. Excellent at Q&A and summarization."},
        {"id": "bigscience/bloom-7b1",                "name": "BLOOM 7B",                  "description": "🌸 Multilingual model (46 languages). Good for translation tasks."},
        {"id": "meta-llama/Llama-3.2-3B-Instruct",   "name": "Llama 3.2 3B Instruct",     "description": "⚡ Meta's compact Llama 3.2. Fast and instruction-tuned."},
        {"id": "Qwen/Qwen2.5-7B-Instruct",            "name": "Qwen 2.5 7B Instruct",      "description": "🀄 Strong multilingual model. Great at coding and reasoning."},
    ]

    FREE_TIER_LIMITS = {
        "tier_name": "Free Serverless Inference API",
        "signup_url": "https://huggingface.co/settings/tokens",
        "dashboard_url": "https://huggingface.co/settings/billing",
        "reset_schedule": "Rate limits are rolling per-hour windows. No daily hard cap (but fair-use enforced).",
        "reset_type": "rolling_minute",
        "global_limits": {
            "requests_per_minute": None,     # Not publicly specified; depends on load
            "requests_per_day": None,        # Fair-use policy; no hard number
            "tokens_per_minute": None,
            "tokens_per_day": None,
            "credit_card_required": False,
        },
        "model_limits": {},
        "notes": [
            "Free tier is for experimentation only — not guaranteed availability.",
            "Very popular models may be slow or temporarily unavailable.",
            "For production use, upgrade to PRO ($9/month) for priority access.",
            "Some models (e.g. gated Llama) require accepting a license on the model page.",
            "No hard documented limit — governed by a fair-use policy.",
            "Check status: https://status.huggingface.co/",
        ],
    }

    @property
    def default_model(self) -> str:
        return "mistralai/Mistral-7B-Instruct-v0.3"

    def chat(self, prompt: str, system: Optional[str] = None) -> str:
        try:
            from huggingface_hub import InferenceClient
        except ImportError:
            raise ImportError("Run:  pip install huggingface_hub")

        client = InferenceClient(token=self.api_key)
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = client.chat_completion(model=self.model, messages=messages, max_tokens=1024)
        return response.choices[0].message.content or ""
