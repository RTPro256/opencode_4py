# Ollama Thinking Modes Guide

> **Navigation:** [OllamaModels](./OllamaModels) - Model-specific documentation

This guide covers thinking mode functionality across Ollama models that support reasoning toggles.

---

## Overview

Thinking modes allow you to control how much reasoning effort a model applies to generate responses. Different models implement this differently:

| Model Family | Mechanism | Toggle Method |
|-------------|-----------|---------------|
| **Qwen3** (qwen3, qwen3-coder) | Dual-mode (think/no_think) | `/think` or `/no_think` in prompts |
| **DeepSeek-R1** | Always-on CoT | Outputs in `<thought>` tags |
| **GPT-Oss** | Configurable depth | Low/Medium/High reasoning effort |

---

## Qwen3 Thinking Modes

The Qwen3 family supports seamless toggling between deep reasoning and fast responses.

### Toggle Commands

- **`/think`** - Enable thinking mode for complex tasks
- **`/no_think`** - Disable thinking for fast, simple responses

### Usage Methods

#### 1. In-Prompt (Ollama/CLI/Direct Chat)

Append the command to your prompt:

```
How many 'r's are in 'strawberries'? /think
Explain quantum physics simply /no_think
What is the complexity of this algorithm? /think
Hello! /no_think
```

#### 2. Python API (Ollama library)

```python
import ollama

# Thinking Mode Enabled
response = ollama.chat(
    model="qwen3:32b",
    messages=[{"role": "user", "content": "Analyze this code... /think"}]
)
print(response["message"]["content"])

# Thinking Mode Disabled (Fast)
response = ollama.chat(
    model="qwen3:32b",
    messages=[{"role": "user", "content": "What is 2+2? /no_think"}]
)
print(response["message"]["content"])
```

#### 3. API/vLLM Parameter (Advanced)

For API integrations with vLLM or OpenAI-compatible servers:

```python
# Enable thinking via extra body parameter
extra_body = {
    "chat_template_kwargs": {
        "enable_thinking": True  # or False
    }
}
```

#### 4. Ollama CLI Setting

Set the mode globally for a session:

```
/set think
/set no_think
```

### Recommended Settings

For optimal results, Qwen recommends:

| Mode | Temperature | Top P | Best For |
|------|-------------|-------|----------|
| Thinking | 0.6 | 0.95 | Complex math, logic, coding |
| Non-Thinking | 0.7 | 0.8 | Fast responses, simple queries |

### Models Supporting Qwen3 Thinking Modes

- [`qwen3_32b`](./qwen3_32b.md) - General-purpose Qwen3 model
- [`qwen3-coder_30b`](./qwen3-coder_30b.md) - Code-specialized Qwen3
- [`qwen3-coder-next_q4_K_M`](./qwen3-coder-next_q4_K_M.md) - Next-gen coder

---

## DeepSeek-R1 Thinking Mode

DeepSeek-R1 uses a different approach - it always generates chain-of-thought reasoning.

### How It Works

- The model is trained with reinforcement learning to "think" before answering
- Reasoning is output in `<thought>` tags for transparency
- Users can verify the logical steps the model took

### Example Output

```
<thought>
Let me count the letters in 'strawberries':
s-t-r-a-w-b-e-r-r-i-e-s
1-2-3-4-5-6-7-8-9-10-11

There are 3 'r's in 'strawberries'.
</thought>
There are 3 'r's in "strawberries".
```

### Models

- [`deepseek-r1_32b`](./deepseek-r1_32b.md) - 32B parameter distilled model

---

## GPT-Oss Configurable Reasoning

GPT-Oss offers three levels of reasoning effort.

### Reasoning Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| **Low** | Fast, minimal reasoning | Simple queries, high throughput |
| **Medium** | Balanced | General tasks |
| **High** | Deep analysis | Complex logic, math, debugging |

### Usage

Use the reasoning effort parameter in your API call:

```python
import ollama

response = ollama.chat(
    model="gpt-oss:20b",
    messages=[{"role": "user", "content": "Analyze this code"}],
    options={
        "reasoning_effort": "high"  # low, medium, or high
    }
)
```

### Models

- [`gpt-oss_20b`](./gpt-oss_20b.md) - 21B MoE model with configurable reasoning

---

## Comparison Matrix

| Model | Toggle Method | Always-On? | Levels? | Best For |
|-------|--------------|------------|---------|----------|
| Qwen3 | `/think`/`/no_think` | No | 2 | General purpose, coding |
| DeepSeek-R1 | None | Yes | 1 | Math, logic, transparency |
| GPT-Oss | Parameter | No | 3 | Flexible reasoning control |

---

## Quick Reference

### Enable Thinking (Qwen3)
```
/think
```

### Disable Thinking (Qwen3)
```
/no_think
```

### Complex Task (Thinking)
```
Write a quicksort implementation in Python with detailed comments. /think
```

### Simple Query (Non-Thinking)
```
What is Python? /no_think
```

---

## Related Documentation

- [Ollama Testing](../OLLAMA_TESTING.md#thinking-mode-tests-qwen3-models) - Integration tests for thinking modes
- [Ollama Testing](../OLLAMA_TESTING.md) - General Ollama integration tests
- [Model Registry](../aimodels/README.md) - Available models overview
