# ERR-003: AI Provider Availability

## Metadata
- **Error ID**: ERR-003
- **Category**: Configuration
- **Severity**: Medium
- **Status**: Fixed
- **Date Encountered**: 2026-02-23
- **Related Errors**: None

## Symptom
Integration fails because the configured AI model is not available in the target environment.

## Root Cause
Integration was tested with a cloud model not available in target environment. No pre-flight checks for provider availability.

## Fix
Added pre-flight checks for Ollama and remote provider configuration:

```python
# Check Ollama
import requests
try:
    response = requests.get("http://localhost:11434/api/tags")
    models = response.json().get("models", [])
    print(f"Available Ollama models: {[m['name'] for m in models]}")
except Exception as e:
    print(f"Ollama not available: {e}")

# Check for remote provider API keys
import os
api_keys = {
    "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
    "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY"),
}
for key, value in api_keys.items():
    status = "configured" if value else "NOT SET"
    print(f"{key}: {status}")
```

## Verification
```bash
# Check Ollama
curl http://localhost:11434/api/tags

# Or check for remote provider API keys
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY
```

## Lesson Learned
Test with the same AI providers that will be available in production.

## Prevention
- Create pre-flight check script that verifies provider availability
- Document required providers in integration guide
- Fail fast with clear error message if provider not available
