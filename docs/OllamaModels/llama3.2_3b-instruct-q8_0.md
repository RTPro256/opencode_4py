## Core Functionality & Architecture

### High-Fidelity 8-bit Quantization (q8_0)
- **8-bit quantization** preserves more original model precision compared to 4-bit versions
- Ideal for tasks requiring:
  - High logical consistency
  - Nuanced understanding
  - Reliable output quality

### Extended 128K Context Window
- **128,000 token context length** despite compact model size
- Enables:
  - Summarizing long documents
  - Maintaining lengthy conversation histories
  - Processing complex multi-turn interactions locally

### Instruction-Tuned Efficiency
- Fine-tuned using:
  - **Supervised Fine-Tuning (SFT)**
  - **Reinforcement Learning from Human Feedback (RLHF)**
- Aligns with human preferences for:
  - Helpfulness
  - Safety
  - Consistent behavior

### Grouped-Query Attention (GQA)
- Optimized transformer architecture for:
  - Improved inference scalability
  - Reduced memory bandwidth usage
  - Efficient parameter utilization

---

## Key Capabilities

- **On-Device Reasoning**  
  - Lightweight local use cases including:
    - Summarization
    - Rewriting tasks
    - Dialogue generation

- **Agentic Retrieval**  
  - Specialized for tool use and agentic workflows
  - Excels in interacting with external data/APIs

- **Multilingual Support**  
  - Officially supports **8 languages**:
    - English, German, French, Italian, Portuguese, Hindi, Spanish, and Thai

- **Benchmark Performance**  
  - Frequently outperforms larger open-source models (e.g., Gemma)
  - Strong results on industry NLP benchmarks for common tasks

---

## Performance & Hardware Profile

- **VRAM Requirements**:  
  - **4GB–8GB VRAM** for smooth operation  
  - Ideal for modern laptops and mobile-class hardware  

- **Low Latency**:  
  - Near-instantaneous responses on consumer hardware  
  - High token-per-second rates due to efficient parameter count  

- **Privacy-First Design**:  
  - Operates entirely locally via **Ollama**  
  - Ensures sensitive data/prompts never leave your device  
` ``
