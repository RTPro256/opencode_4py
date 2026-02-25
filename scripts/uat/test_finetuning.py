"""
UAT script for fine-tuning module validation.
Run: python scripts/uat/test_finetuning.py
"""

import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src" / "opencode" / "src"
sys.path.insert(0, str(src_path))

# Use ASCII characters for Windows compatibility
PASS = "[PASS]"
FAIL = "[FAIL]"


def test_imports():
    """Test that all fine-tuning components can be imported."""
    print("Testing fine-tuning module imports...")
    
    try:
        from opencode.core.finetuning import (
            LoRAConfig,
            TrainingConfig,
            FineTuningConfig,
            DatasetPreparer,
            AlpacaFormatter,
            ChatFormatter,
            TrainingSample,
        )
        print(f"{PASS} All fine-tuning components imported successfully")
        return True
    except ImportError as e:
        print(f"{FAIL} Import failed: {e}")
        return False


def test_config_creation():
    """Test creating configuration instances."""
    print("\nTesting configuration creation...")
    
    try:
        from opencode.core.finetuning import LoRAConfig, TrainingConfig, FineTuningConfig
        
        lora = LoRAConfig(r=16, lora_alpha=32)
        print(f"{PASS} LoRAConfig created: r={lora.r}, alpha={lora.lora_alpha}")
        
        training = TrainingConfig(num_train_epochs=3, per_device_train_batch_size=4)
        print(f"{PASS} TrainingConfig created: epochs={training.num_train_epochs}")
        
        finetune = FineTuningConfig(model_name="test-model")
        print(f"{PASS} FineTuningConfig created: model={finetune.model_name}")
        
        return True
    except Exception as e:
        print(f"{FAIL} Configuration creation failed: {e}")
        return False


def test_dataset_preparation():
    """Test dataset preparation components."""
    print("\nTesting dataset preparation...")
    
    try:
        from opencode.core.finetuning import (
            DatasetPreparer,
            AlpacaFormatter,
            ChatFormatter,
            TrainingSample,
        )
        
        preparer = DatasetPreparer()
        print(f"{PASS} DatasetPreparer created")
        
        alpaca = AlpacaFormatter()
        sample = TrainingSample(instruction="Test", input="", output="Result")
        formatted = alpaca.format_sample(sample)
        print(f"{PASS} AlpacaFormatter works: length={len(formatted)}")
        
        chat = ChatFormatter()
        sample = TrainingSample(instruction="Hello", output="Hi there!")
        formatted = chat.format_sample(sample)
        print(f"{PASS} ChatFormatter works: length={len(formatted)}")
        
        return True
    except Exception as e:
        print(f"{FAIL} Dataset preparation failed: {e}")
        return False


def main():
    """Run all UAT tests for fine-tuning module."""
    print("=" * 60)
    print("Fine-tuning Module User Acceptance Testing")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Config Creation", test_config_creation()))
    results.append(("Dataset Preparation", test_dataset_preparation()))
    
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
