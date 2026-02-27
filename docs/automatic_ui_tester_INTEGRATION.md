# automatic_ui_tester Integration

## Overview

This document describes the integration of the Multi-AI Client provider system from `merge_projects/automatic_ui_tester` into opencode_4py.

## Source Project

**Project**: automatic_ui_tester
**Version**: files (7) - Final version with full Multi-AI Client
**Location**: `merge_projects/automatic_ui_tester/files (7)/`

## Features Integrated

### 1. Multi-AI Provider System

A unified interface for connecting to multiple AI providers with consistent API:

| Provider | Model | Free Tier | API Key Env Var |
|----------|-------|-----------|-----------------|
| OpenAI | GPT-3.5, GPT-4o | $5 trial credits | `OPENAI_API_KEY` |
| Google AI | Gemini 1.5 Flash/Pro | 15 RPM, 1500 RPD | `GOOGLE_AI_API_KEY` |
| Anthropic | Claude Haiku/Sonnet/Opus | 5 RPM | `ANTHROPIC_API_KEY` |
| Ollama | Local models | Unlimited | (none required) |
| Groq | Llama 3, Mixtral | 30 RPM | `GROQ_API_KEY` |
| HuggingFace | Mistral, Llama | Fair use | `HUGGINGFACE_API_KEY` |
| OpenRouter | Various free models | 20 RPM, 200 RPD | `OPENROUTER_API_KEY` |
| GitHub Models | GPT-4o, Llama 3 | 15 RPM, 150 RPD | `GITHUB_TOKEN` |

### 2. Model Picker CLI

Interactive terminal interface for exploring and selecting models:

```bash
# Browse all available models
opencode model-picker

# View configuration instructions
opencode model-picker --configure
```

Features:
- Browse all free models across providers
- Interactive model selection
- Test chat with any provider
- Interactive chat sessions
- Usage dashboard

### 3. Usage Tracking

Local tracking of API usage per provider:
- Requests per day
- Estimated tokens (prompt + response)
- Data stored in `~/.opencode/usage_data.json`

### 4. Limits Dashboard

Visual display of:
- Current usage vs limits
- Progress bars for daily limits
- Reset countdowns
- Provider-specific tips

## Architecture

```
src/opencode/src/opencode/core/providers/
├── __init__.py          # Exports all providers
├── base.py              # BaseProvider abstract class
├── client.py            # MultiAIClient main class
├── usage_tracker.py     # Local usage tracking
├── openai_provider.py   # OpenAI implementation
├── google_provider.py   # Google AI (Gemini)
├── anthropic_provider.py # Anthropic (Claude)
├── ollama_provider.py   # Ollama (local)
├── groq_provider.py     # Groq
├── huggingface_provider.py # HuggingFace
├── openrouter_provider.py # OpenRouter
└── github_provider.py   # GitHub Models
```

## Usage

### Basic Usage

```python
from opencode.core.providers import (
    MultiAIClient,
    OpenAIProvider,
    GoogleAIProvider,
)

# Create client and add providers
client = MultiAIClient()
client.add("openai", OpenAIProvider(api_key="sk-..."))
client.add("gemini", GoogleAIProvider(api_key="..."))

# Chat with a specific provider
response = client.chat("openai", "Hello! How are you?")

# List all free models
client.browse_all_models()

# Interactive model picker
client.pick_model("openai")

# Show usage dashboard
client.show_dashboard()
```

### CLI Usage

```bash
# Start interactive model picker
opencode model-picker

# Configure providers
opencode model-picker --configure
```

## Configuration

Set API keys as environment variables:

```bash
# .env file
OPENAI_API_KEY=sk-...
GOOGLE_AI_API_KEY=...
ANTHROPIC_API_KEY=sk-ant-...
GROQ_API_KEY=...
HUGGINGFACE_API_KEY=hf_...
OPENROUTER_API_KEY=...
GITHUB_TOKEN=ghp_...
```

## Integration Notes

- The provider system uses a consistent interface via `BaseProvider`
- All providers support the same `chat()` method signature
- Model catalogs and limits are built into each provider
- Usage tracking is automatic but can be disabled

## Testing

Run the model picker:

```bash
cd src/opencode
python -m opencode.cli.commands.model_picker
```

## Dependencies

Required packages (per provider):
- `openai` - OpenAI, OpenRouter, GitHub Models
- `google-generativeai` - Google AI
- `anthropic` - Anthropic
- `groq` - Groq
- `huggingface_hub` - HuggingFace

## Future Enhancements

- [ ] Add more providers (Azure OpenAI, Cohere, etc.)
- [ ] Support for function calling
- [ ] Streaming responses
- [ ] Token counting from API responses
- [ ] Integration with opencode's existing LLM configuration
