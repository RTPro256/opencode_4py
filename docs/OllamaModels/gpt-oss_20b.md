## Core Functionality & Architecture

### Mixture-of-Experts (MoE)
- **21B total parameters** with **~3.6B active per token** during inference  
- Significantly faster and more memory-efficient than dense models of similar size

### Native MXFP4 Quantization
- Post-trained with **4.25-bit quantization** for MoE weights  
- **Ollama-compatible** format runs in as little as **16GB VRAM**  
- No additional quality loss compared to unquantized versions

### 128K Context Window
- Supports **128,000 token context length** for:
  - Processing extensive documents
  - Analyzing large codebases
  - Managing complex multi-turn conversations

### Chain-of-Thought (CoT) Reasoning
- Native "thinking" model that generates internal reasoning steps before final answers  
- Enhances transparency and reliability in complex tasks

---

## Key Features

### Configurable Reasoning Effort
- Adjustable "thinking" depth with three modes:
  - **Low** (fast)
  - **Medium** (balanced)
  - **High** (deep analysis)
- Trade speed for accuracy based on task requirements

### Agentic Capabilities
- Native support for:
  - **Function calling**
  - **Web browsing**
  - **Python code execution**
- Optimized for autonomous tool use to solve complex tasks

### Transparency
- Full access to the model's reasoning process (the "analysis channel")
- Facilitates debugging of logic and tool interactions

### OpenAI Compatibility
- Fully compatible with **OpenAI Responses API**
- Easy drop-in replacement for self-hosted OpenAI workflows

---

## Hardware Requirements

- **Minimum VRAM**:  
  - **16GB** (e.g., NVIDIA RTX 4070 Ti, 4080, or 3090/4090)  

- **Recommended Setup**:  
  - High-end consumer GPUs  
  - Apple Silicon Macs with unified memory (M2/M3 Max/Ultra)  
  - Ideal for low-latency performance  
