## Core Functionalities

### Chain-of-Thought (CoT) Reasoning
- Designed to "think" before answering
- In Ollama, outputs internal reasoning process in `<thought>` tags
- Allows users to verify logical steps and reasoning

### Advanced Mathematical & Logical Solving
- Excels at complex, multi-step problem solving
- Achieves benchmark scores in:
  - **Math**: AIME24
  - **Logic**: Performance nearly identical to full 671B parameter model

### Coding Proficiency
- Optimized for code generation and understanding
- Supports autonomous coding agents
- Handles functional coding tasks
- May prioritize detailed reasoning over immediate execution in complex scenarios

### Extended Context Management
- Supports **128k token context window**
- Suitable for:
  - Analyzing long documents
  - Processing large codebases
  - Maintaining extensive conversation histories

---

## Technical Specifications

| Feature                  | Description                                                                 |
|--------------------------|-----------------------------------------------------------------------------|
| Base Architecture        | Distilled from DeepSeek-R1 using Qwen-2.5-32B                              |
| Parameter Count          | 32 Billion                                                                  |
| VRAM Requirement         | ~20GB to 32GB depending on quantization                                    |
| Training Method          | Reinforcement Learning (RL) via Group Relative Policy Optimization (GRPO)  |
| License                  | MIT License (permits commercial use and modification)                      |

---

## Best Use Cases

- **Local RAG Systems**  
  - Large context window and factual retrieval capabilities  
  - Ideal for Retrieval-Augmented Generation (RAG) tasks  

- **Private Research**  
  - Runs entirely offline via Ollama  
  - Processes sensitive data without compromising privacy  

- **Technical Assistance**  
  - Deep explanations for STEM subjects  
  - Complex logic-based queries for students and developers  
` ``
