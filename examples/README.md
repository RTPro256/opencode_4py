# OpenCode Python Examples

This directory contains example code demonstrating how to use OpenCode Python.

## Prerequisites

Install the package:

```bash
pip install opencode-python
```

Or install from source:

```bash
cd src/opencode
pip install -e .
```

## Examples

### Basic Usage

[`basic_usage.py`](basic_usage.py) - Demonstrates the basic usage of OpenCode:
- Initializing the client
- Sending messages to an LLM
- Handling responses

```bash
python examples/basic_usage.py
```

### RAG (Retrieval-Augmented Generation)

[`rag_example.py`](rag_example.py) - Demonstrates RAG capabilities:
- Setting up a RAG pipeline
- Indexing documents
- Querying with context retrieval

```bash
python examples/rag_example.py
```

### Provider Configuration

[`provider_config.py`](provider_config.py) - Demonstrates provider configuration:
- Configuring different LLM providers (OpenAI, Anthropic, Ollama)
- Using environment variables for API keys
- Switching between providers

```bash
# Set API keys as needed
export OPENAI_API_KEY="your-key"
export ANTHROPIC_API_KEY="your-key"

python examples/provider_config.py
```

## Configuration

OpenCode can be configured via:

1. **Environment variables** - Set `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.
2. **Config file** - Create `~/.config/opencode/config.toml`
3. **Command line** - Pass options when running

Example config file:

```toml
[provider]
default = "openai"

[provider.openai]
api_key = "your-api-key"
model = "gpt-4"

[provider.anthropic]
api_key = "your-api-key"
model = "claude-3-opus-20240229"
```

## More Resources

- [Documentation](../docs/)
- [Contributing](../CONTRIBUTING.md)
- [Main README](../README.md)