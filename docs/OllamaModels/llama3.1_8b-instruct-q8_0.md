## Core Functionality & Architecture

### 8-bit Quantization (q8_0)
- Uses **8-bit integers** to store weights
- Considered the "sweet spot" for 8B models:
  - Eliminates quality degradation seen in 4-bit or lower quantizations
  - Balances performance and memory efficiency

### Massive 128K Context Window
- **Defining upgrade** in the 3.1 series:
  - Supports up to **128,000 tokens**
  - Processes entire technical manuals or long conversation histories in single prompts

### Grouped-Query Attention (GQA)
- Optimized for:
  - **Fast inference speeds**
  - **Lower memory bandwidth usage**
  - Smooth, real-time responses on consumer-grade hardware

### Multilingual Training
- Native support and high proficiency in **8 primary languages**:
  - English, German, French, Italian, Portuguese, Hindi, Spanish, and Thai

---

## Primary Use Cases

- **Advanced Tool Use & Agents**  
  - Optimized for tool calling and structured JSON outputs  
  - Robust backend for autonomous agents  

- **Complex Instruction Following**  
  - Refined via **Direct Preference Optimization (DPO)**  
  - Excels at multi-step logic and maintaining factual accuracy  
  - Outperforms base Llama 3 models in this domain  

- **RAG & Document Analysis**  
  - Leverages 128K context window for **Retrieval-Augmented Generation (RAG)**  
  - Efficiently searches and summarizes large text volumes  

- **On-Device Development**  
  - Ideal for local chatbots/coding assistants  
  - High intelligence with single-laptop/desktop deployment  

---

## Performance & Hardware Requirements

- **RAM/VRAM**:  
  - **q8_0 version** requires at least **16GB VRAM** (e.g., NVIDIA RTX 3090/4070 Ti Super)  
  - Or **16GB system RAM** on unified memory systems (e.g., Apple Silicon)  

- **Inference Speed**:  
  - Capable of **60–100 tokens/second** on modern GPUs  
  - Maintains speed while preserving quality  
` ``
