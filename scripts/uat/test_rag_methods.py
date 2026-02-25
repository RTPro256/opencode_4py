"""
UAT script for RAG methods validation.
Run: python scripts/uat/test_rag_methods.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src" / "opencode" / "src"
sys.path.insert(0, str(src_path))

from typing import List, Dict, Any

# Use ASCII characters for Windows compatibility
PASS = "[PASS]"
FAIL = "[FAIL]"


def test_imports():
    """Test that all RAG methods can be imported."""
    print("Testing RAG method imports...")
    
    try:
        from opencode.core.rag.methods import (
            BaseRAGMethod,
            RAGMethodConfig,
            RAGResult,
            RetrievedDocument,
            create_rag_method,
            get_available_methods,
        )
        print(f"{PASS} Core imports successful")
        
        # Test lazy loading of each method
        methods = get_available_methods()
        print(f"{PASS} Found {len(methods)} registered methods: {', '.join(methods)}")
        return True
    except ImportError as e:
        print(f"{FAIL} Import failed: {e}")
        return False


def test_registry():
    """Test the RAG method registry."""
    print("\nTesting RAG method registry...")
    
    from opencode.core.rag.methods import get_available_methods
    
    methods = get_available_methods()
    print(f"Available methods: {methods}")
    
    # Core methods that should always be available
    core_methods = {"naive", "hyde", "self", "corrective", "graph", "fusion", "reranker", "advanced", "agentic"}
    
    if core_methods.issubset(set(methods)):
        print(f"{PASS} All {len(core_methods)} core methods registered")
        return True
    else:
        missing = core_methods - set(methods)
        print(f"{FAIL} Missing core methods: {missing}")
        return False


async def test_instantiation():
    """Test creating RAG method instances."""
    print("\nTesting RAG method instantiation...")
    
    from opencode.core.rag.methods import create_rag_method, RAGMethodConfig
    
    config = RAGMethodConfig(top_k=5)
    
    # Test core methods
    methods_to_test = ["naive", "hyde", "self", "corrective", "graph", "fusion", "reranker", "advanced", "agentic"]
    results = {}
    
    for method_name in methods_to_test:
        try:
            rag = create_rag_method(method_name, config)
            results[method_name] = PASS if rag is not None else FAIL
        except Exception as e:
            results[method_name] = f"{FAIL} ({type(e).__name__}: {e})"
    
    print("Instantiation results:")
    for method, status in results.items():
        print(f"  {method}: {status}")
    
    return all(PASS in v for v in results.values())


def test_config():
    """Test RAG configuration."""
    print("\nTesting RAG configuration...")
    
    from opencode.core.rag.methods import RAGMethodConfig
    from opencode.core.rag.methods.base import RetrievalStrategy, ChunkingStrategy
    
    try:
        # Test default config
        config = RAGMethodConfig()
        print(f"{PASS} Default config created: top_k={config.top_k}")
        
        # Test custom config
        config = RAGMethodConfig(
            top_k=10,
            similarity_threshold=0.5,
            retrieval_strategy=RetrievalStrategy.HYBRID,
        )
        print(f"{PASS} Custom config created: top_k={config.top_k}, strategy={config.retrieval_strategy}")
        
        return True
    except Exception as e:
        print(f"{FAIL} Config test failed: {e}")
        return False


def test_result_classes():
    """Test RAG result classes."""
    print("\nTesting RAG result classes...")
    
    from opencode.core.rag.methods import RAGResult, RetrievedDocument
    
    try:
        # Test RetrievedDocument
        doc = RetrievedDocument(
            content="Test document content",
            metadata={"source": "test"},
            score=0.95,
        )
        print(f"{PASS} RetrievedDocument created: score={doc.score}")
        
        # Test RAGResult
        result = RAGResult(
            answer="Test answer",
            sources=[doc],
            confidence=0.9,
        )
        print(f"{PASS} RAGResult created: confidence={result.confidence}")
        
        return True
    except Exception as e:
        print(f"{FAIL} Result classes test failed: {e}")
        return False


def main():
    """Run all UAT tests for RAG methods."""
    print("=" * 60)
    print("RAG Methods User Acceptance Testing")
    print("=" * 60)
    
    results = []
    
    # Test 1: Imports
    results.append(("Imports", test_imports()))
    
    # Test 2: Registry
    results.append(("Registry", test_registry()))
    
    # Test 3: Instantiation
    results.append(("Instantiation", asyncio.run(test_instantiation())))
    
    # Test 4: Config
    results.append(("Configuration", test_config()))
    
    # Test 5: Result classes
    results.append(("Result Classes", test_result_classes()))
    
    # Summary
    print("\n" + "=" * 60)
    print("UAT Summary")
    print("=" * 60)
    
    passed = sum(1 for _, v in results if v)
    total = len(results)
    
    for name, status in results:
        print(f"  {name}: {PASS if status else FAIL}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
