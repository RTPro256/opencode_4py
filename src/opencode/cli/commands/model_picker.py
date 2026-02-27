"""
Model Picker CLI Command

An interactive terminal tool for exploring and selecting free AI models
across all configured providers.

Usage:
    opencode model-picker
    opencode model-picker --configure
"""

import os
import sys
from typing import Optional

import click

from opencode.core.providers import (
    MultiAIClient,
    OpenAIProvider,
    GoogleAIProvider,
    AnthropicProvider,
    OllamaProvider,
    GroqProvider,
    HuggingFaceProvider,
    OpenRouterProvider,
    GitHubModelsProvider,
)


def build_client() -> tuple[MultiAIClient, int]:
    """Register all providers that have keys in environment."""
    client = MultiAIClient()

    providers_to_try = [
        ("gemini", "GOOGLE_AI_API_KEY", GoogleAIProvider),
        ("huggingface", "HUGGINGFACE_API_KEY", HuggingFaceProvider),
        ("openrouter", "OPENROUTER_API_KEY", OpenRouterProvider),
        ("groq", "GROQ_API_KEY", GroqProvider),
        ("github", "GITHUB_TOKEN", GitHubModelsProvider),
        ("openai", "OPENAI_API_KEY", OpenAIProvider),
        ("claude", "ANTHROPIC_API_KEY", AnthropicProvider),
        ("ollama", None, OllamaProvider),  # No API key needed
    ]

    registered = 0
    for name, env_var, cls in providers_to_try:
        if env_var:
            key = os.getenv(env_var)
            if key:
                client.add(name, cls(api_key=key))
                registered += 1
        else:
            # Special handling for Ollama (no API key)
            try:
                ollama = cls(api_key="")
                if ollama.is_running():
                    client.add(name, ollama)
                    registered += 1
            except Exception:
                pass

    return client, registered


def clear_line():
    print()


def header(text: str):
    width = 60
    print(f"\n{'═'*width}")
    print(f"  {text}")
    print(f"{'═'*width}")


def section(text: str):
    print(f"\n{'─'*60}")
    print(f"  {text}")
    print(f"{'─'*60}")


def prompt_choice(options: list[str], allow_back: bool = True) -> int:
    """
    Show a numbered menu and return the 0-based index of the user's choice.
    Returns -1 if the user chooses to go back.
    """
    for i, opt in enumerate(options, start=1):
        print(f"  [{i}] {opt}")
    if allow_back:
        print(f"  [0] ← Back")
    print()

    while True:
        raw = input("  Enter number: ").strip()
        if allow_back and raw == "0":
            return -1
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        print(f"  ⚠️  Please enter a number between 1 and {len(options)}.")


def screen_browse_all(client: MultiAIClient):
    """Show every provider's free models in one overview."""
    client.browse_all_models()
    input("  Press Enter to return to the main menu...")


def screen_pick_model(client: MultiAIClient):
    """Let the user choose a provider, then pick a model interactively."""
    providers = client.list_providers()
    if not providers:
        print("\n  ⚠️  No providers registered. Check your .env file or run with --configure.")
        return

    section("Pick a provider")
    idx = prompt_choice(providers)
    if idx == -1:
        return

    client.pick_model(providers[idx])


def screen_test_chat(client: MultiAIClient):
    """Send a quick test message to verify the selected model works."""
    providers = client.list_providers()
    if not providers:
        print("\n  ⚠️  No providers registered. Check your .env file.")
        return

    section("Choose a provider to test")
    idx = prompt_choice(providers)
    if idx == -1:
        return

    name = providers[idx]
    provider = client._get_provider(name)

    print(f"\n  Provider : {name}")
    print(f"  Model    : {provider.model}")

    info = provider.current_model_info()
    if info:
        print(f"  About    : {info['description']}")

    print()
    test_prompt = input("  Enter a test message (or press Enter for a default): ").strip()
    if not test_prompt:
        test_prompt = "In one sentence, what can you help me with?"

    print(f"\n  ⏳ Sending to '{name}'...\n")
    try:
        reply = client.chat(name, test_prompt)
        print(f"  💬 Reply:\n")
        # Indent the reply for readability
        for line in reply.splitlines():
            print(f"     {line}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

    print()
    input("  Press Enter to return to the main menu...")


def screen_interactive_chat(client: MultiAIClient):
    """Full interactive chat session with a chosen provider/model."""
    providers = client.list_providers()
    if not providers:
        print("\n  ⚠️  No providers registered. Check your .env file.")
        return

    section("Choose a provider to chat with")
    idx = prompt_choice(providers)
    if idx == -1:
        return

    name = providers[idx]
    provider = client._get_provider(name)

    print(f"\n  ✅  Chatting with [{name}] using model [{provider.model}]")
    print(f"  Commands: 'quit' · 'switch' (change model) · 'info' · 'limits' · 'usage'\n")

    while True:
        try:
            user_input = input("  You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  Goodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit", "q"):
            print("  Goodbye!")
            break

        if user_input.lower() == "switch":
            client.pick_model(name)
            print(f"  Now using: {provider.model}\n")
            continue

        if user_input.lower() == "info":
            info = provider.current_model_info()
            if info:
                print(f"\n  Model : {info['name']}")
                print(f"  About : {info['description']}")
                print(f"  ID    : {info['id']}\n")
            else:
                print(f"\n  Current model: {provider.model} (no extra info available)\n")
            continue

        if user_input.lower() == "limits":
            client.show_limits(name)
            continue

        if user_input.lower() == "usage":
            client.show_usage()
            continue

        try:
            reply = client.chat(name, user_input)
            print(f"\n  AI: {reply}\n")
        except Exception as e:
            print(f"\n  ❌  Error: {e}\n")


@click.command()
@click.option("--configure", is_flag=True, help="Show configuration instructions")
def main(configure: bool):
    """Interactive model picker for all configured AI providers."""
    if configure:
        header("🤖  Provider Configuration")
        print("""
  To use providers, set their API keys as environment variables:

  ┌─────────────────────────┬────────────────────────────────────┐
  │ Provider                │ Environment Variable               │
  ├─────────────────────────┼────────────────────────────────────┤
  │ OpenAI                  │ OPENAI_API_KEY                     │
  │ Google AI (Gemini)      │ GOOGLE_AI_API_KEY                 │
  │ Anthropic (Claude)      │ ANTHROPIC_API_KEY                 │
  │ Ollama (local)          │ (none - runs locally)             │
  │ Groq                    │ GROQ_API_KEY                      │
  │ HuggingFace             │ HUGGINGFACE_API_KEY               │
  │ OpenRouter              │ OPENROUTER_API_KEY                 │
  │ GitHub Models           │ GITHUB_TOKEN                      │
  └─────────────────────────┴────────────────────────────────────┘

  Get free API keys from:
  • OpenAI: https://platform.openai.com/api-keys
  • Google: https://aistudio.google.com/app/apikey
  • Anthropic: https://console.anthropic.com/settings/keys
  • Groq: https://console.groq.com/keys
  • HuggingFace: https://huggingface.co/settings/tokens
  • OpenRouter: https://openrouter.ai/keys
  • GitHub: https://github.com/settings/tokens
  • Ollama: https://ollama.com
        """)
        return

    header("🤖  Multi-AI Model Picker")
    print("  Explore and switch between free AI models across providers.\n")

    client, registered = build_client()

    if registered == 0:
        print("  ❌  No API keys found.")
        print("      Run with --configure to see how to set up providers.\n")
        sys.exit(1)

    MENU = [
        "Browse all free models (overview)",
        "Pick a model for a provider",
        "Test a quick message",
        "Start an interactive chat session",
        "📊  View limits & usage dashboard",
        "Exit",
    ]

    while True:
        section("Main Menu")
        idx = prompt_choice(MENU, allow_back=False)

        if idx == 0:
            screen_browse_all(client)
        elif idx == 1:
            screen_pick_model(client)
        elif idx == 2:
            screen_test_chat(client)
        elif idx == 3:
            screen_interactive_chat(client)
        elif idx == 4:
            client.show_dashboard()
            input("  Press Enter to continue...")
        elif idx == 5:
            print("\n  Goodbye! 👋\n")
            sys.exit(0)


if __name__ == "__main__":
    main()
