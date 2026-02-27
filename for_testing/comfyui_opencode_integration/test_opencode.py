"""Test script for OpenCode_4py integration"""
import asyncio
import sys

async def test_ollama():
    from opencode.llmchecker.ollama import OllamaClient
    c = OllamaClient()
    models = await c.list_models()
    # list_models returns a list of OllamaModel objects
    print('Ollama models found:', len(models) if models else 0)
    for m in models[:5] if models else []:
        print(f"  - {m.name}")
    return models

async def test_gpu():
    from opencode.core.gpu_manager import GPUManager
    g = GPUManager()
    # Use the correct async method
    gpus = await g.get_available_gpus()
    print('GPUs detected:', len(gpus) if gpus else 0)
    for gpu in gpus[:2] if gpus else []:
        print(f"  - {gpu}")
    return gpus

if __name__ == "__main__":
    print("=" * 50)
    print("OpenCode_4py Integration Test")
    print("=" * 50)
    
    print("\n1. Testing Ollama connection...")
    try:
        asyncio.run(test_ollama())
        print("   [OK] Ollama connection successful")
    except Exception as e:
        print(f"   [ERROR] Ollama connection failed: {e}")
    
    print("\n2. Testing GPU detection...")
    try:
        asyncio.run(test_gpu())
        print("   [OK] GPU detection successful")
    except Exception as e:
        print(f"   [ERROR] GPU detection failed: {e}")
    
    print("\n" + "=" * 50)
    print("Integration test complete!")
    print("=" * 50)
