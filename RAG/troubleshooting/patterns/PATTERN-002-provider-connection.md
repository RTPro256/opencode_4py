# PATTERN-002: Provider Connection Diagnosis

## Metadata
- **Pattern ID**: PATTERN-002
- **Category**: Diagnosis Pattern
- **Applies To**: AI provider connection issues

## Symptoms
- "Connection refused" errors
- "Timeout" errors
- "Model not found" errors
- No response from AI provider

## Diagnosis Steps

### Step 1: Check Ollama Status
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Check available models
curl http://localhost:11434/api/tags | jq '.models[].name'
```

### Step 2: Verify Model Availability
```bash
# List installed models
ollama list

# Pull required model if not installed
ollama pull llama3.2
```

### Step 3: Test Provider Directly
```python
import requests

# Test Ollama connection
response = requests.post(
    "http://localhost:11434/api/generate",
    json={"model": "llama3.2", "prompt": "Hello", "stream": False}
)
print(response.json())
```

### Step 4: Check Configuration
```python
# Verify config has correct model
from opencode.core.config import Config

config = Config.load()
print(f"Model: {config.model}")
print(f"Provider: {config.provider}")
```

## Common Causes

| Error | Cause | Fix |
|-------|-------|-----|
| Connection refused | Ollama not running | Start Ollama service |
| Model not found | Model not installed | `ollama pull <model>` |
| Timeout | Network/firewall issue | Check firewall settings |
| API key invalid | Wrong API key | Check environment variables |

## Related Errors
- ERR-003: AI Provider Availability
- ERR-007: Wrong Provider Class
- ERR-009: Wrong Provider Method Name

## Prevention
- Run pre-flight checks before starting application
- Include provider status in TUI sidebar
- Add health check endpoint for providers
