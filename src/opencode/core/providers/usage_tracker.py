"""
usage_tracker.py — tracks how many requests and tokens you've used
per provider, per day. Saves data to a local JSON file so it
persists between runs.

This is a LOCAL counter — it counts what YOUR CODE sends.
It does not fetch live data from the provider's servers.

Usage:
    tracker = UsageTracker()
    tracker.record("groq", prompt="Hello!", response="Hi there!")
    tracker.show_today()
"""

import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional


# Where usage data is saved
USAGE_FILE = Path.home() / ".opencode" / "usage_data.json"

# Rough token estimator: 1 token ≈ 4 characters (good enough for tracking)
def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


class UsageTracker:
    """
    Records and retrieves local usage statistics.

    Data is stored in ~/.opencode/usage_data.json
    Structure:
        {
            "groq": {
                "2024-01-15": {
                    "requests": 12,
                    "prompt_tokens": 840,
                    "response_tokens": 1200
                }
            }
        }
    """

    def __init__(self, filepath: Path = USAGE_FILE):
        self.filepath = filepath
        # Ensure directory exists
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict = self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> dict:
        """Load saved usage data from disk, or return empty dict."""
        if self.filepath.exists():
            try:
                with open(self.filepath, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save(self) -> None:
        """Write current usage data to disk."""
        with open(self.filepath, "w") as f:
            json.dump(self._data, f, indent=2)

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record(
        self,
        provider_name: str,
        prompt: str = "",
        response: str = "",
        prompt_tokens: Optional[int] = None,
        response_tokens: Optional[int] = None,
    ) -> None:
        """
        Record one API call for a provider.

        Args:
            provider_name:   e.g. "groq", "gemini"
            prompt:          The text you sent (used to estimate tokens)
            response:        The text you received (used to estimate tokens)
            prompt_tokens:   If you know the exact count, pass it here
            response_tokens: If you know the exact count, pass it here
        """
        today = str(date.today())

        p_tokens = prompt_tokens if prompt_tokens is not None else _estimate_tokens(prompt)
        r_tokens = response_tokens if response_tokens is not None else _estimate_tokens(response)

        # Ensure nested dicts exist
        self._data.setdefault(provider_name, {})
        self._data[provider_name].setdefault(today, {
            "requests": 0,
            "prompt_tokens": 0,
            "response_tokens": 0,
        })

        day = self._data[provider_name][today]
        day["requests"] += 1
        day["prompt_tokens"] += p_tokens
        day["response_tokens"] += r_tokens

        self._save()

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get_today(self, provider_name: str) -> dict:
        """
        Return today's usage for one provider.
        Returns zeroed dict if no usage recorded yet.
        """
        today = str(date.today())
        return self._data.get(provider_name, {}).get(today, {
            "requests": 0,
            "prompt_tokens": 0,
            "response_tokens": 0,
        })

    def get_all_today(self) -> dict:
        """Return today's usage for every tracked provider."""
        today = str(date.today())
        result = {}
        for provider, days in self._data.items():
            result[provider] = days.get(today, {
                "requests": 0,
                "prompt_tokens": 0,
                "response_tokens": 0,
            })
        return result

    def get_history(self, provider_name: str, days: int = 7) -> list[dict]:
        """
        Return the last N days of usage for a provider.
        Returns a list of dicts sorted newest-first, each with a "date" key added.
        """
        from datetime import timedelta
        provider_data = self._data.get(provider_name, {})
        result = []
        for i in range(days):
            day = str(date.today() - timedelta(days=i))
            entry = provider_data.get(day, {
                "requests": 0,
                "prompt_tokens": 0,
                "response_tokens": 0,
            })
            result.append({"date": day, **entry})
        return result

    def reset_today(self, provider_name: str) -> None:
        """Clear today's usage for one provider (useful for testing)."""
        today = str(date.today())
        if provider_name in self._data and today in self._data[provider_name]:
            del self._data[provider_name][today]
            self._save()
            print(f"🗑️  Cleared today's usage for '{provider_name}'")

    def reset_all(self) -> None:
        """⚠️ Wipe ALL recorded usage data."""
        self._data = {}
        self._save()
        print("🗑️  All usage data cleared.")

    def total_requests(self, provider_name: str) -> int:
        """Total requests ever recorded for a provider."""
        total = 0
        for day_data in self._data.get(provider_name, {}).values():
            total += day_data.get("requests", 0)
        return total

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def show_today(self, provider_name: Optional[str] = None) -> None:
        """Print a simple summary of today's usage."""
        if provider_name:
            data = {provider_name: self.get_today(provider_name)}
        else:
            data = self.get_all_today()

        print(f"\n  📊  Usage today ({date.today()})")
        print(f"  {'─'*50}")
        for name, stats in data.items():
            total_tok = stats["prompt_tokens"] + stats["response_tokens"]
            print(f"  {name:15s}  {stats['requests']:4d} requests   ~{total_tok:6,d} tokens")
        print()
