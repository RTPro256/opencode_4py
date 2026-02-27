## Core Functionality & Architecture

### Dual-Mode Reasoning
- **Thinking Mode**: For complex logic, math, and coding tasks  
- **Non-Thinking Mode**: For rapid, general-purpose dialogue  
- Seamless switching between modes for optimal performance  

### Massive Context Window
- **Native support**: 32K token context  
- **Extended support**: Up to **131,072 tokens** using YaRN scaling  
- Ideal for analyzing long documents and repositories  

### Advanced Parameter Density
- **64 transformer layers** with **Grouped-Query Attention (GQA)**  
- Optimized balance between high-quality output and inference speed  

### Multilingual Mastery
- Supports **100+ languages and dialects**  
- Improved cultural awareness and translation accuracy  

---

## Key Capabilities

### State-of-the-Art Reasoning
- In **Thinking Mode**, rivals or surpasses models like **QwQ-32B** and **DeepSeek-R1**  
- Excels in **complex mathematics** and **logical deduction**  

### Agentic Power
- Optimized for **tool use** and **multi-agent collaboration**  
- Native support for **Model Context Protocol (MCP)** for external API/database interaction  

### Coding Excellence
- Trained on **7.5 trillion tokens** with high code ratio  
- Specialized in **multi-turn debugging** and **repository-scale code generation**  

---

## Thinking Modes (Detailed Guide)

Qwen3-32B supports dual-mode reasoning, allowing you to toggle between deep thinking and fast responses:

### Toggle Modes
- **Thinking Mode** (`/think`): For complex logic, math, and coding tasks  
- **Non-Thinking Mode** (`/no_think`): For rapid, general-purpose dialogue

### Usage Methods

#### 1. In-Prompt (Ollama/CLI/Direct Chat)
Append `/think` or `/no_think` to your prompt:
```
How many 'r's are in 'strawberries'? /think
Explain quantum physics simply /no_think
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
For API integrations (e.g., vLLM or OpenAI-compatible servers):
```python
extra_body={
    "chat_template_kwargs": {
        "enable_thinking": True  # or False
    }
}
```

#### 4. Ollama CLI Setting
```
/set think
/set no_think
```

### Recommended Settings for Best Results

| Mode | Temperature | Top P | Use Case |
|------|-------------|-------|----------|
| Thinking | 0.6 | 0.95 | Complex math, logic, coding |
| Non-Thinking | 0.7 | 0.8 | Fast responses, simple queries |

---

## Ollama Usage Tips

- **Thinking Toggle**:  
  - Use `/think` or `/no_think` in prompts to dynamically control reasoning mode (if backend supports soft-switch mechanism)  

- **Hardware Requirements**:  
  - **32B dense model** requires **24GB–32GB VRAM** for local execution at **4-bit or 8-bit quantization**  
