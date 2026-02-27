"""
MultiAIClient — a single object that talks to many AI providers.

Features:
  - Automatic usage tracking on every .chat() call
  - client.show_limits("groq")     — see a provider's free-tier rules
  - client.show_all_limits()       — see all providers at a glance
  - client.show_usage()            — see how much you've used today
  - client.show_dashboard()        — limits + usage combined view
"""

from datetime import datetime, timezone
from typing import Dict, Optional

from .base import BaseProvider
from .usage_tracker import UsageTracker


class MultiAIClient:
    """
    Manages multiple AI provider connections under friendly names.
    Automatically tracks your usage on every chat() call.
    """

    def __init__(self, track_usage: bool = True):
        """
        Args:
            track_usage: Set to False to disable local usage tracking.
        """
        self._providers: Dict[str, BaseProvider] = {}
        self._tracker = UsageTracker() if track_usage else None

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def add(self, name: str, provider: BaseProvider) -> None:
        """Register a provider under a nickname."""
        self._providers[name] = provider
        print(f"✅  Added provider '{name}' → {provider}")

    def remove(self, name: str) -> None:
        """Remove a provider by its nickname."""
        if name in self._providers:
            del self._providers[name]
            print(f"🗑️  Removed provider '{name}'")

    def list_providers(self) -> list[str]:
        """Return the names of all registered providers."""
        return list(self._providers.keys())

    # ------------------------------------------------------------------
    # Model browsing & selection
    # ------------------------------------------------------------------

    def list_free_models(self, provider_name: str) -> list[dict]:
        """Return the free-model catalog for a given provider."""
        return self._get_provider(provider_name).list_free_models()

    def list_all_free_models(self) -> Dict[str, list[dict]]:
        """Return free-model catalogs for ALL registered providers."""
        return {name: p.list_free_models() for name, p in self._providers.items()}

    def set_model(self, provider_name: str, model_id: str) -> None:
        """Switch a provider to a different model."""
        self._get_provider(provider_name).set_model(model_id)

    def pick_model(self, provider_name: str) -> None:
        """Interactive numbered menu to choose a model for a provider."""
        provider = self._get_provider(provider_name)
        models = provider.list_free_models()

        if not models:
            print(f"⚠️  No free-model catalog available for '{provider_name}'.")
            return

        print(f"\n{'─'*60}")
        print(f"  Free models for  ›  {provider_name.upper()}  ‹")
        print(f"  Currently using  :  {provider.model}")
        print(f"{'─'*60}")

        for i, m in enumerate(models, start=1):
            marker = " ◀ current" if m["id"] == provider.model else ""
            print(f"  [{i}]  {m['name']}{marker}")
            print(f"        {m['description']}")
            print(f"        id: {m['id']}")
            print()

        print(f"{'─'*60}")
        print(f"  Enter a number to switch, or press Enter to keep current.")

        while True:
            choice = input("  Your choice: ").strip()
            if choice == "":
                print(f"  Keeping current model: {provider.model}")
                break
            if choice.isdigit() and 1 <= int(choice) <= len(models):
                selected = models[int(choice) - 1]
                provider.set_model(selected["id"])
                print(f"  ✅  Now using: {selected['name']}")
                break
            print(f"  Please enter a number between 1 and {len(models)}, or press Enter.")
        print(f"{'─'*60}\n")

    def browse_all_models(self) -> None:
        """Print a full overview of free models across all providers."""
        if not self._providers:
            print("No providers registered yet.")
            return

        print(f"\n{'═'*60}")
        print("  FREE MODEL CATALOG — ALL PROVIDERS")
        print(f"{'═'*60}")

        for name, provider in self._providers.items():
            models = provider.list_free_models()
            print(f"\n  ▶  {name.upper()}  (current: {provider.model})")
            print(f"  {'─'*56}")
            if not models:
                print("     No catalog available.")
            else:
                for m in models:
                    marker = " ◀" if m["id"] == provider.model else ""
                    print(f"     • {m['name']}{marker}")
                    print(f"       {m['description']}")

        print(f"\n{'═'*60}")
        print("  Tip: use client.pick_model('<provider>') to switch models.")
        print(f"{'═'*60}\n")

    # ------------------------------------------------------------------
    # Limits
    # ------------------------------------------------------------------

    def show_limits(self, provider_name: str) -> None:
        """
        Print a detailed breakdown of the free-tier limits for one provider.

        Shows:
          - Tier name & reset schedule
          - Global limits
          - Limits for the currently active model
          - Tips and notes
          - Links to the dashboard and docs
        """
        provider = self._get_provider(provider_name)
        limits = provider.get_limits()

        if not limits:
            print(f"  ⚠️  No limit data available for '{provider_name}'.")
            return

        w = 60
        print(f"\n{'═'*w}")
        print(f"  🔒  FREE TIER LIMITS — {provider_name.upper()}")
        print(f"{'═'*w}")
        print(f"  Plan      : {limits.get('tier_name', 'N/A')}")
        print(f"  Reset     : {limits.get('reset_schedule', 'N/A')}")
        print(f"  Sign-up   : {limits.get('signup_url', 'N/A')}")
        print(f"  Dashboard : {limits.get('dashboard_url', 'N/A')}")

        # Global limits
        gl = limits.get("global_limits", {})
        if gl:
            print(f"\n  {'─'*56}")
            print(f"  Global limits (all models):")
            _print_limit_row("  Requests / minute", gl.get("requests_per_minute"))
            _print_limit_row("  Requests / day   ", gl.get("requests_per_day"))
            _print_limit_row("  Tokens / minute  ", gl.get("tokens_per_minute"))
            _print_limit_row("  Tokens / day     ", gl.get("tokens_per_day"))
            if "credit_card_required" in gl:
                req = "Yes" if gl["credit_card_required"] else "No"
                print(f"  Card required    : {req}")
            if "new_user_credits_usd" in gl:
                print(f"  New user credits : ${gl['new_user_credits_usd']:.2f}")
            if "free_trial_credit_usd" in gl:
                print(f"  Trial credits    : ${gl['free_trial_credit_usd']:.2f}  "
                      f"(expires after {gl.get('trial_expires_days', '?')} days)")

        # Current model limits
        model_lim = provider.get_model_limits()
        if model_lim:
            print(f"\n  {'─'*56}")
            print(f"  Limits for current model: {provider.model}")
            _print_limit_row("  Requests / minute", model_lim.get("requests_per_minute"))
            _print_limit_row("  Requests / day   ", model_lim.get("requests_per_day"))
            _print_limit_row("  Tokens / minute  ", model_lim.get("tokens_per_minute"))
            _print_limit_row("  Tokens / day     ", model_lim.get("tokens_per_day"))

        # Notes
        notes = limits.get("notes", [])
        if notes:
            print(f"\n  {'─'*56}")
            print(f"  📝  Tips & caveats:")
            for note in notes:
                print(f"     • {note}")

        print(f"{'═'*w}\n")

    def show_all_limits(self) -> None:
        """
        Print a compact overview of free-tier limits for ALL registered providers.
        Great for quickly comparing which provider has the most headroom.
        """
        if not self._providers:
            print("No providers registered yet.")
            return

        w = 72
        print(f"\n{'═'*w}")
        print(f"  🔒  FREE TIER LIMITS — ALL PROVIDERS")
        print(f"{'═'*w}")
        print(f"  {'Provider':<14} {'Plan':<26} {'RPM':>5} {'RPD':>7} {'TPM':>9}  Reset")
        print(f"  {'─'*68}")

        for name, provider in self._providers.items():
            limits = provider.get_limits()
            if not limits:
                print(f"  {name:<14} {'No data available'}")
                continue

            ml = provider.get_model_limits()
            rpm = _fmt_num(ml.get("requests_per_minute"))
            rpd = _fmt_num(ml.get("requests_per_day"))
            tpm = _fmt_num(ml.get("tokens_per_minute"))
            reset = limits.get("reset_type", "?")
            tier = limits.get("tier_name", "Free")[:25]

            print(f"  {name:<14} {tier:<26} {rpm:>5} {rpd:>7} {tpm:>9}  {reset}")

        print(f"  {'─'*68}")
        print(f"  RPM = requests/min  RPD = requests/day  TPM = tokens/min")
        print(f"  '?' = not publicly documented  '∞' = no stated limit")
        print(f"\n  Tip: client.show_limits('<provider>') for full detail + notes.")
        print(f"{'═'*w}\n")

    # ------------------------------------------------------------------
    # Usage tracking
    # ------------------------------------------------------------------

    def show_usage(self) -> None:
        """Print today's local usage (requests + estimated tokens) per provider."""
        if not self._tracker:
            print("Usage tracking is disabled (pass track_usage=True to enable).")
            return
        self._tracker.show_today()

    def show_dashboard(self) -> None:
        """
        The main event — shows limits + today's usage + % remaining
        for every registered provider. Includes reset countdown.
        """
        if not self._providers:
            print("No providers registered yet.")
            return

        from datetime import date
        today_usage = self._tracker.get_all_today() if self._tracker else {}

        w = 68
        print(f"\n{'═'*w}")
        print(f"  📊  USAGE DASHBOARD  —  {date.today()}")
        print(f"{'═'*w}")

        for name, provider in self._providers.items():
            limits = provider.get_limits()
            model_lim = provider.get_model_limits() if limits else {}
            usage = today_usage.get(name, {"requests": 0, "prompt_tokens": 0, "response_tokens": 0})

            used_req = usage["requests"]
            used_tok = usage["prompt_tokens"] + usage["response_tokens"]

            print(f"\n  ▶  {name.upper()}  │  model: {provider.model}")
            print(f"  {'─'*64}")

            if limits:
                tier = limits.get("tier_name", "Free")
                reset = limits.get("reset_schedule", "See provider dashboard")
                print(f"     Plan    : {tier}")
                print(f"     Resets  : {reset}")

            # Requests bar
            rpd = model_lim.get("requests_per_day") if model_lim else None
            print(f"\n     Requests today : {used_req:,}", end="")
            if rpd:
                pct = min(100, used_req / rpd * 100)
                remaining = max(0, rpd - used_req)
                bar = _progress_bar(pct)
                print(f" / {rpd:,}   {bar}  {pct:.0f}%  ({remaining:,} left)")
            else:
                print(f"  (no daily request limit documented)")

            # Tokens bar
            tpd = model_lim.get("tokens_per_day") if model_lim else None
            print(f"     Tokens today   : {used_tok:,}", end="")
            if tpd:
                pct = min(100, used_tok / tpd * 100)
                remaining = max(0, tpd - used_tok)
                bar = _progress_bar(pct)
                print(f" / {tpd:,}   {bar}  {pct:.0f}%  ({remaining:,} left)")
            else:
                print(f"  (no daily token limit documented)")

            if limits:
                dash = limits.get("dashboard_url", "")
                if dash:
                    print(f"\n     📎  Live usage : {dash}")

        # Reset countdown
        print(f"\n  {'─'*64}")
        _print_reset_countdown()
        print(f"\n  ℹ️   Token counts are estimated locally (1 token ≈ 4 chars).")
        print(f"       For exact counts, check each provider's dashboard above.")
        print(f"{'═'*w}\n")

    def reset_usage(self, provider_name: Optional[str] = None) -> None:
        """
        Clear locally tracked usage.
        Pass a provider name to clear just that provider, or omit to clear all.
        """
        if not self._tracker:
            return
        if provider_name:
            self._tracker.reset_today(provider_name)
        else:
            confirm = input("⚠️  Clear ALL recorded usage data? (yes/no): ").strip().lower()
            if confirm == "yes":
                self._tracker.reset_all()

    # ------------------------------------------------------------------
    # Chatting
    # ------------------------------------------------------------------

    def chat(
        self,
        provider_name: str,
        prompt: str,
        system: Optional[str] = None,
    ) -> str:
        """
        Send a message to one specific provider.
        Usage is automatically recorded locally.
        """
        provider = self._get_provider(provider_name)
        response = provider.chat(prompt, system=system)

        # Record usage
        if self._tracker:
            self._tracker.record(provider_name, prompt=prompt, response=response)

        return response

    def chat_all(
        self,
        prompt: str,
        system: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Send the same prompt to EVERY registered provider and collect results.
        Usage is recorded for each provider automatically.
        """
        results: Dict[str, str] = {}
        for name in self._providers:
            print(f"⏳  Asking '{name}' ({self._providers[name].model})...")
            try:
                results[name] = self.chat(name, prompt, system=system)
            except Exception as exc:
                results[name] = f"[ERROR] {exc}"
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_provider(self, name: str) -> BaseProvider:
        if name not in self._providers:
            available = ", ".join(self._providers.keys()) or "none"
            raise ValueError(
                f"Provider '{name}' not found. Available: {available}"
            )
        return self._providers[name]

    def __repr__(self) -> str:
        return f"MultiAIClient(providers={list(self._providers.keys())})"


# ── Module-level formatting helpers ───────────────────────────────────

def _fmt_num(value) -> str:
    """Format a number nicely, showing '?' for None."""
    if value is None:
        return "?"
    if value >= 1_000_000:
        return f"{value/1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value/1_000:.0f}K"
    return str(value)


def _print_limit_row(label: str, value) -> None:
    if value is None:
        print(f"{label} : not documented")
    else:
        print(f"{label} : {value:,}")


def _progress_bar(pct: float, width: int = 12) -> str:
    """Return a text progress bar like [████░░░░░░░░]."""
    filled = int(width * pct / 100)
    empty = width - filled
    color = "🟥" if pct >= 90 else ("🟨" if pct >= 60 else "🟩")
    return f"[{'█'*filled}{'░'*empty}] {color}"


def _print_reset_countdown() -> None:
    """Print how long until midnight UTC (the most common reset time)."""
    now = datetime.now(timezone.utc)
    from datetime import timedelta
    next_midnight = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    delta = next_midnight - now
    hours, remainder = divmod(int(delta.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    print(f"  ⏰  Next reset in: {hours}h {minutes}m {seconds}s (midnight UTC)")
