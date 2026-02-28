"""
Ollama provider — run AI models LOCALLY on your own computer. 100% free, unlimited.

SETUP (one time):
  1. Download and install Ollama from: https://ollama.com
  2. Pull a model, e.g.:   ollama pull llama3.2
  3. Ollama runs as a background service at http://localhost:11434

No API key needed — your computer IS the server.
Models run offline once downloaded.

Browse available models at: https://ollama.com/library
"""

import json
import urllib.request
import urllib.error
from typing import Optional

from opencode.core.defaults import OLLAMA_BASE_URL, DEFAULT_OLLAMA_URL

from .base import BaseProvider


# Where Ollama listens by default (kept for backwards compatibility)
OLLAMA_BASE_URL = OLLAMA_BASE_URL


class OllamaProvider(BaseProvider):
    """
    Connects to a locally-running Ollama instance.

    Unlike all other providers, Ollama:
    - Requires NO API key (pass api_key="" or any string)
    - Lists your ACTUALLY INSTALLED models dynamically
    - Works completely offline
    - Has NO rate limits or token limits whatsoever
    """

    # A curated list of popular models you can pull — shown in the picker
    # even if not yet installed, so users know what's available.
    FREE_MODELS = [
        {
            "id": "llama3.2",
            "name": "Llama 3.2 (3B)",
            "description": "⚡ Meta's compact model. Fast on most hardware. Pull: ollama pull llama3.2",
        },
        {
            "id": "llama3.2:1b",
            "name": "Llama 3.2 (1B)",
            "description": "⚡⚡ Tiny but capable. Runs on almost any machine. Pull: ollama pull llama3.2:1b",
        },
        {
            "id": "llama3.1",
            "name": "Llama 3.1 (8B)",
            "description": "🧠 Meta's 8B model. Great quality/speed balance. Pull: ollama pull llama3.1",
        },
        {
            "id": "llama3.1:70b",
            "name": "Llama 3.1 (70B)",
            "description": "🚀 Powerful 70B model. Needs ~40GB RAM. Pull: ollama pull llama3.1:70b",
        },
        {
            "id": "mistral",
            "name": "Mistral 7B",
            "description": "🌟 Excellent open model. Fast and well-rounded. Pull: ollama pull mistral",
        },
        {
            "id": "gemma2",
            "name": "Gemma 2 (9B)",
            "description": "🔷 Google's open model. Strong at reasoning. Pull: ollama pull gemma2",
        },
        {
            "id": "gemma2:2b",
            "name": "Gemma 2 (2B)",
            "description": "🔷 Tiny Google model. Very fast on CPU. Pull: ollama pull gemma2:2b",
        },
        {
            "id": "phi3",
            "name": "Phi-3 Mini",
            "description": "🔬 Microsoft's small powerhouse. Pull: ollama pull phi3",
        },
        {
            "id": "qwen2.5",
            "name": "Qwen 2.5 (7B)",
            "description": "🀄 Strong at code and reasoning. Pull: ollama pull qwen2.5",
        },
        {
            "id": "deepseek-r1",
            "name": "DeepSeek R1 (7B)",
            "description": "💡 Reasoning model. Shows thinking steps. Pull: ollama pull deepseek-r1",
        },
        {
            "id": "codellama",
            "name": "Code Llama (7B)",
            "description": "💻 Optimised for coding tasks. Pull: ollama pull codellama",
        },
        {
            "id": "nomic-embed-text",
            "name": "Nomic Embed Text",
            "description": "📐 Text embeddings model (not for chat). Pull: ollama pull nomic-embed-text",
        },
    ]

    FREE_TIER_LIMITS = {
        "tier_name": "Local — Unlimited",
        "signup_url": "https://ollama.com",
        "dashboard_url": "http://localhost:11434",
        "reset_schedule": "No limits — runs locally on your hardware.",
        "reset_type": "none",
        "global_limits": {
            "requests_per_minute": None,   # unlimited
            "requests_per_day": None,      # unlimited
            "tokens_per_minute": None,     # unlimited
            "tokens_per_day": None,        # unlimited
            "credit_card_required": False,
        },
        "model_limits": {},
        "notes": [
            "✅  100% free and unlimited — you pay only for electricity.",
            "✅  Works completely offline after the model is downloaded.",
            "✅  Your data never leaves your computer — maximum privacy.",
            "⚠️  Speed depends on your hardware (GPU speeds things up a lot).",
            "⚠️  Large models (30B+) require significant RAM (16–64GB).",
            "💡  Start with llama3.2 or gemma2:2b for fast results on any machine.",
            "💡  Install Ollama from: https://ollama.com",
            "💡  Pull a model: run  ollama pull llama3.2  in your terminal.",
        ],
    }

    def __init__(self, api_key: str = "", model: Optional[str] = None,
                 base_url: str = OLLAMA_BASE_URL):
        """
        Args:
            api_key:  Not needed for Ollama — pass "" or omit.
            model:    Model name to use (e.g. "llama3.2"). If None, uses
                      the first installed model, or "llama3.2" as fallback.
            base_url: Ollama server URL. Change if running on another machine.
        """
        self.base_url = base_url.rstrip("/")
        # We need base_url set before calling super().__init__
        # because default_model may call get_installed_models()
        super().__init__(api_key=api_key, model=model)

    @property
    def default_model(self) -> str:
        """Use the first installed model, or suggest llama3.2 if none found."""
        installed = self.get_installed_models()
        if installed:
            return installed[0]["id"]
        return "llama3.2"

    # ------------------------------------------------------------------
    # Ollama-specific methods
    # ------------------------------------------------------------------

    def is_running(self) -> bool:
        """Return True if an Ollama server is reachable at base_url."""
        try:
            with urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=3) as r:
                return r.status == 200
        except Exception:
            return False

    def get_installed_models(self) -> list[dict]:
        """
        Return a list of models currently installed on this Ollama instance.
        Each entry has "id", "name", and "description" (size info).

        Returns an empty list if Ollama is not running.
        """
        try:
            with urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=3) as r:
                data = json.loads(r.read().decode())
        except Exception:
            return []

        result = []
        for m in data.get("models", []):
            name = m.get("name", "")
            size_bytes = m.get("size", 0)
            size_gb = size_bytes / 1_073_741_824
            size_str = f"{size_gb:.1f} GB" if size_gb >= 1 else f"{size_bytes // 1_048_576} MB"
            result.append({
                "id": name,
                "name": name,
                "description": f"💾 Installed locally ({size_str})",
            })
        return result

    def pull_model(self, model_id: str) -> None:
        """
        Print instructions for pulling a model (we don't run shell commands
        automatically, but we tell the user exactly what to do).
        """
        print(f"\n  To install '{model_id}', run this in your terminal:")
        print(f"\n      ollama pull {model_id}\n")
        print(f"  Then restart this script.\n")

    # ------------------------------------------------------------------
    # Override list_free_models to show installed + popular models
    # ------------------------------------------------------------------

    @classmethod
    def list_free_models(cls) -> list[dict]:
        """
        Return the curated list of popular Ollama models.
        For actually-installed models, call get_installed_models() on an instance.
        """
        return cls.FREE_MODELS

    def list_installed_and_popular(self) -> dict:
        """
        Return both installed models and the popular models catalog.

        Returns:
            {
                "installed": [...],   # models on THIS machine
                "popular":   [...],   # curated list from FREE_MODELS
            }
        """
        return {
            "installed": self.get_installed_models(),
            "popular": self.FREE_MODELS,
        }

    # ------------------------------------------------------------------
    # Chat
    # ------------------------------------------------------------------

    def chat(self, prompt: str, system: Optional[str] = None) -> str:
        """Send a message to the local Ollama server."""
        if not self.is_running():
            raise ConnectionError(
                "Ollama is not running!\n"
                "  1. Install Ollama from https://ollama.com\n"
                "  2. Start it (it runs as a background service)\n"
                f"  3. Make sure it's reachable at {self.base_url}"
            )

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = json.dumps({
            "model": self.model,
            "messages": messages,
            "stream": False,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read().decode())
                return data["message"]["content"]
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if "model" in body.lower() and "not found" in body.lower():
                raise ValueError(
                    f"Model '{self.model}' is not installed.\n"
                    f"Run:  ollama pull {self.model}"
                ) from e
            raise
