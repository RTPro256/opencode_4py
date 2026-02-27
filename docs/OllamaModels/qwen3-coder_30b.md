## Key Functional Capabilities

### Advanced Agentic Coding (SWE-Bench Specialist)
- Optimized for **agentic workflows**:
  - Understands entire repositories
  - Plans multi-step solutions
  - Uses tools and fixes bugs (SWE-Bench)

### Massive Long-Context Window
- Native context window: **256,000 tokens**
- Extendable up to **1M tokens** with techniques
- Enables analysis/refactoring/documentation of massive, multi-file codebases

### MoE Efficiency (High Performance, Lower VRAM)
- **30B parameter footprint** with Mixture-of-Experts (MoE) architecture:
  - Only **3.3B parameters** activated per token during inference
  - Faster performance on consumer hardware (24GB-48GB VRAM)
  - More efficient than dense 30B models

### Extensive Training & Coding Focus
- Pretrained on **7.5 trillion tokens** (70% code-centric)
- High-quality generation across **dozens of programming languages**

### Specialized Tool Calling
- Optimized for integration with IDE extensions:
  - Cline
  - Qwen Code CLI
  - Enables autonomous coding tasks

---

## Performance & Specifications (Ollama)

- **Architecture**: Sparse Mixture-of-Experts (128 total experts, 8 activated per task)
- **Context**: 262,144 tokens (native)
- **Best Use Cases**:
  - Complex debugging
  - Repository-level understanding
  - Autonomous agentic coding
  - Multi-turn programming
  - Code explanation
- **Recommended Setup**:
  - Use **Q5_K_XL** or **Q8_0** quantization versions
  - Optimized for high-end consumer GPUs (e.g., RTX 3090/4090 with >24GB VRAM)
  - Balances accuracy and hardware efficiency

---

## Thinking Modes (Qwen3 Feature)

Qwen3-Coder supports the dual-mode reasoning system from the Qwen3 series:

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
    model="qwen3-coder:30b",
    messages=[{"role": "user", "content": "Debug this function... /think"}]
)

# Thinking Mode Disabled (Fast)
response = ollama.chat(
    model="qwen3-coder:30b",
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

## Comparison with Qwen3-30B-Instruct

- **Qwen3-Coder:30b vs Base Qwen3-30B**:
  - **Base model**: Better for general chat/reasoning
  - **Coder variant**: Specifically fine-tuned for:
    - Code generation
    - Tool usage
    - "Tool-call happy" behavior
  - **User experience**: Better at code-based solutions vs general text
