# OpenCode Configuration Presets

This directory contains configuration presets for common OpenCode setups.

---

## Available Presets

| Preset | Description | Requirements |
|--------|-------------|--------------|
| [`claude.toml`](claude.toml) | Anthropic Claude configuration | `ANTHROPIC_API_KEY` |
| [`openai.toml`](openai.toml) | OpenAI GPT configuration | `OPENAI_API_KEY` |
| [`local.toml`](local.toml) | Local Ollama configuration | Ollama installed |
| [`multi-provider.toml`](multi-provider.toml) | Multi-provider setup | Multiple API keys |

---

## Usage

### Option 1: Copy to Project

```bash
# Copy a preset to your project
cp config/presets/claude.toml ./opencode.toml

# Edit as needed
nano opencode.toml
```

### Option 2: Merge with Existing Config

Add the relevant sections from a preset to your existing `opencode.toml`.

### Option 3: Use with Profiles

The `multi-provider.toml` preset includes profile definitions:

```bash
# Use development profile
opencode --profile development

# Use local profile
opencode --profile local

# Use fast profile (Groq)
opencode --profile fast
```

---

## Environment Variables

Set the required environment variables before using a preset:

```bash
# For Claude
export ANTHROPIC_API_KEY=your-key-here

# For OpenAI
export OPENAI_API_KEY=your-key-here

# For Google Gemini
export GOOGLE_API_KEY=your-key-here

# For Groq
export GROQ_API_KEY=your-key-here

# For Mistral
export MISTRAL_API_KEY=your-key-here

# For xAI
export XAI_API_KEY=your-key-here
```

---

## Local Setup (Ollama)

For the `local.toml` preset, install and run Ollama:

```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama
ollama serve

# Pull a model
ollama pull llama3.2

# Pull embedding model for RAG
ollama pull nomic-embed-text
```

---

## Customization

### Adjust Model Parameters

```toml
[provider.anthropic]
model = "claude-sonnet-4-20250514"
max_tokens = 8192        # Increase for longer responses
temperature = 0.7        # Lower for more deterministic output
```

### Add Permissions

```toml
[permissions]
bash_allow = [
    "git status",
    "npm test",           # Add project-specific commands
    "make build",
]
```

### Enable MCP Servers

```toml
[mcp]
servers = ["filesystem", "github"]

[mcp.filesystem]
root = "/path/to/project"

[mcp.github]
# GitHub MCP configuration
```

---

## Troubleshooting

### API Key Not Found

```
Error: ANTHROPIC_API_KEY not found
```

**Solution**: Ensure the environment variable is set:
```bash
export ANTHROPIC_API_KEY=your-key-here
```

### Ollama Connection Failed

```
Error: Cannot connect to Ollama at http://localhost:11434
```

**Solution**: Start Ollama:
```bash
ollama serve
```

### Model Not Available

```
Error: Model 'llama3.2' not found
```

**Solution**: Pull the model:
```bash
ollama pull llama3.2
```

---

*Last updated: 2026-02-24*
