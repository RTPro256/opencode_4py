## Core Functionality

### Agentic Coding Expert
- **Trained on 800K+ executable tasks**
- Ideal for:
  - Coding agents
  - Complex tool usage
  - Debugging
  - Beyond basic chat capabilities

### Ultra-Efficient Architecture
- **80B parameter model** with sparse MoE design:
  - Activates only **~3B parameters per token**
  - Enables **fast, cost-effective inference** on local machines

### High-Quantization Precision
- **q4_K_M (4-bit quantization)** version:
  - Fits into **~46GB VRAM**
  - Maintains high accuracy despite reduced precision

### Massive Context Window
- **256K native context length**:
  - Reads entire code repositories
  - Maintains coherence in:
    - Long-session debugging
    - Feature development

### Instantaneous IDE Integration
- Designed for seamless integration with:
  - Cline
  - Claude Code
  - Qwen Code
  - Enables **real-time coding assistance**

---

## Best Use Cases

- **Local AI Agent**  
  - Powers autonomous coding agents (e.g., in VS Code)  
  - Reads, writes, and debugs code  
  - Avoids API costs  

- **Repository-Level Context**  
  - Analyzes and understands large projects  
  - Leverages 256K context for comprehensive insights  

- **Data Privacy**  
  - Runs complex coding tasks **entirely offline**  
  - Ensures sensitive code stays local  

---

## Thinking Modes (Qwen3 Feature)

Qwen3-Coder-Next supports the dual-mode reasoning system from the Qwen3 series:

### Toggle Modes
- **Thinking Mode**: Use `/think` in your prompt for complex logic, math, and coding tasks
- **Non-Thinking Mode**: Use `/no_think` for fast, simple responses

### Usage Methods

#### In-Prompt (Ollama/CLI/Direct Chat)
```
Analyze this code... /think
What is 2+2? /no_think
```

#### Python API (Ollama library)
```python
import ollama

# Thinking Mode Enabled
response = ollama.chat(
    model="qwen3-coder-next",
    messages=[{"role": "user", "content": "Debug this function... /think"}]
)

# Thinking Mode Disabled (Fast)
response = ollama.chat(
    model="qwen3-coder-next",
    messages=[{"role": "user", "content": "What is 2+2? /no_think"}]
)
```

#### Ollama CLI Setting
```
/set think
/set no_think
```

### Recommended Settings
- **Thinking Mode**: temperature=0.6, top_p=0.95
- **Non-Thinking Mode**: temperature=0.7, top_p=0.8

---

## Technical Specifications

- **Total Parameters**: 80B (MoE)  
- **Active Parameters**: ~3B  
- **Context Length**: 256,144 tokens  
- **Quantization**: q4_K_M (Medium 4-bit)  
- **Architecture**: Hybrid Attention + MoE  
