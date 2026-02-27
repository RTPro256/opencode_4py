#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pre-flight Check for OpenCode_4py Integration

This script verifies that all prerequisites are met before running OpenCode_4py.
Run this script before attempting to use OpenCode_4py with ComfyUI.

Usage:
    python check_prerequisites.py
"""

import sys
import os
import subprocess
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Tuple, List, Optional

# Fix Windows console encoding for Unicode characters
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class PreflightChecker:
    """Checks all prerequisites for OpenCode_4py integration."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.successes = []
        self.base_dir = Path(__file__).parent
        
    def print_header(self, title: str) -> None:
        """Print a section header."""
        print("\n" + "=" * 60)
        print(f"  {title}")
        print("=" * 60)
    
    def print_result(self, name: str, status: str, message: str = "") -> None:
        """Print a check result."""
        symbols = {
            "OK": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️",
            "INFO": "ℹ️"
        }
        symbol = symbols.get(status, "❓")
        print(f"  {symbol} {name}: {message}")
        
        if status == "OK":
            self.successes.append(name)
        elif status == "ERROR":
            self.errors.append((name, message))
        elif status == "WARNING":
            self.warnings.append((name, message))
    
    def check_python_version(self) -> bool:
        """Check Python version is 3.10+."""
        self.print_header("Python Environment")
        
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        if version.major >= 3 and version.minor >= 10:
            self.print_result("Python Version", "OK", f"v{version_str}")
            return True
        else:
            self.print_result("Python Version", "ERROR", 
                f"v{version_str} - Need Python 3.10+")
            return False
    
    def check_ollama_installed(self) -> bool:
        """Check if Ollama is installed."""
        self.print_header("Ollama Installation")
        
        # Check if ollama command exists
        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    ["where", "ollama"], 
                    capture_output=True, 
                    text=True,
                    timeout=10
                )
            else:
                result = subprocess.run(
                    ["which", "ollama"], 
                    capture_output=True, 
                    text=True,
                    timeout=10
                )
            
            if result.returncode == 0:
                path = result.stdout.strip().split('\n')[0]
                self.print_result("Ollama Installed", "OK", f"Found at {path}")
                return True
            else:
                self.print_result("Ollama Installed", "ERROR", "Not found in PATH")
                print("\n  📥 RECOMMEND: Install Ollama from https://ollama.ai")
                print("     Windows: Download from https://ollama.ai/download")
                print("     Linux/Mac: curl -fsSL https://ollama.ai/install.sh | sh")
                return False
        except Exception as e:
            self.print_result("Ollama Installed", "ERROR", f"Check failed: {e}")
            return False
    
    def check_ollama_running(self) -> bool:
        """Check if Ollama server is running."""
        self.print_header("Ollama Server")
        
        try:
            response = urllib.request.urlopen(
                "http://localhost:11434/api/version",
                timeout=5
            )
            data = json.loads(response.read())
            version = data.get("version", "unknown")
            self.print_result("Ollama Server", "OK", f"Running v{version}")
            return True
        except urllib.error.URLError:
            self.print_result("Ollama Server", "ERROR", "Not running on localhost:11434")
            print("\n  🚀 RECOMMEND: Start Ollama server:")
            print("     Run: ollama serve")
            print("     Or run Ollama application to start in background")
            return False
        except Exception as e:
            self.print_result("Ollama Server", "ERROR", f"Check failed: {e}")
            return False
    
    def check_ollama_models(self, required_models: Optional[List[str]] = None) -> Tuple[bool, List[str]]:
        """Check available Ollama models."""
        self.print_header("Ollama Models")
        
        if required_models is None:
            required_models = ["llama3.2"]  # Default required model
        
        try:
            response = urllib.request.urlopen(
                "http://localhost:11434/api/tags",
                timeout=10
            )
            data = json.loads(response.read())
            models = data.get("models", [])
            
            if not models:
                self.print_result("Models Available", "ERROR", "No models installed")
                print("\n  📦 RECOMMEND: Install at least one model:")
                for model in required_models:
                    print(f"     Run: ollama pull {model}")
                return False, []
            
            # List available models
            model_names = [m.get("name", "") for m in models]
            self.print_result("Models Available", "OK", f"{len(models)} models found")
            
            print("\n  Installed models:")
            for m in models:
                name = m.get("name", "unknown")
                size = m.get("size", 0) / (1024**3)  # Convert to GB
                details = m.get("details", {})
                params = details.get("parameter_size", "unknown")
                print(f"    - {name} ({size:.1f} GB, {params})")
            
            # Check for required models
            missing_models = []
            for required in required_models:
                found = any(required in name for name in model_names)
                if found:
                    self.print_result(f"Required Model '{required}'", "OK", "Installed")
                else:
                    self.print_result(f"Required Model '{required}'", "WARNING", "Not found")
                    missing_models.append(required)
            
            if missing_models:
                print(f"\n  📦 RECOMMEND: Install missing models:")
                for model in missing_models:
                    print(f"     Run: ollama pull {model}")
            
            return len(missing_models) == 0, model_names
            
        except urllib.error.URLError:
            self.print_result("Models Check", "ERROR", "Cannot connect to Ollama")
            return False, []
        except Exception as e:
            self.print_result("Models Check", "ERROR", f"Check failed: {e}")
            return False, []
    
    def check_remote_providers(self) -> bool:
        """Check if any remote AI providers are configured."""
        self.print_header("Remote AI Providers")
        
        # Check for API keys in environment or config
        providers = [
            ("OPENAI_API_KEY", "OpenAI", "https://platform.openai.com/api-keys"),
            ("ANTHROPIC_API_KEY", "Anthropic (Claude)", "https://console.anthropic.com/"),
            ("GOOGLE_API_KEY", "Google (Gemini)", "https://aistudio.google.com/app/apikey"),
            ("GROQ_API_KEY", "Groq", "https://console.groq.com/keys"),
            ("OPENROUTER_API_KEY", "OpenRouter", "https://openrouter.ai/keys"),
            ("MISTRAL_API_KEY", "Mistral", "https://console.mistral.ai/"),
            ("COHERE_API_KEY", "Cohere", "https://dashboard.cohere.com/api-keys"),
        ]
        
        configured = []
        for env_var, name, url in providers:
            api_key = os.environ.get(env_var)
            if api_key:
                self.print_result(f"{name}", "OK", f"API key found in {env_var}")
                configured.append(name)
            else:
                self.print_result(f"{name}", "INFO", f"Not configured")
        
        if configured:
            print(f"\n  ✅ Configured providers: {', '.join(configured)}")
            return True
        else:
            print("\n  ℹ️  No remote AI providers configured.")
            print("  To use remote AI providers, set API keys in environment variables:")
            for env_var, name, url in providers[:4]:  # Show top 4
                print(f"    - {name}: set {env_var}=your-api-key")
            print(f"\n  Or edit opencode.toml to add API keys directly.")
            return False  # Not an error, just info
    
    def check_gpu(self) -> bool:
        """Check GPU availability."""
        self.print_header("GPU Detection")
        
        try:
            # Try nvidia-smi first
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                gpus = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
                if gpus:
                    self.print_result("NVIDIA GPU", "OK", f"{len(gpus)} GPU(s) found")
                    for i, gpu in enumerate(gpus):
                        print(f"    GPU {i}: {gpu}")
                    return True
            
            # Check for other GPU backends
            self.print_result("NVIDIA GPU", "WARNING", "No NVIDIA GPUs detected")
            print("\n  ℹ️ OpenCode_4py can run on CPU, but GPU is recommended for better performance")
            return True  # Not a failure, just a warning
            
        except FileNotFoundError:
            self.print_result("NVIDIA GPU", "WARNING", "nvidia-smi not found")
            print("\n  ℹ️ OpenCode_4py can run on CPU, but GPU is recommended")
            return True  # Not a failure
        except Exception as e:
            self.print_result("GPU Check", "WARNING", f"Check failed: {e}")
            return True  # Not a failure
    
    def check_dependencies(self) -> bool:
        """Check required Python packages."""
        self.print_header("Python Dependencies")
        
        required_packages = [
            ("rich", "TUI rendering"),
            ("textual", "TUI framework"),
            ("tiktoken", "Token counting"),
            ("pydantic", "Data validation"),
            ("aiohttp", "Async HTTP"),
            ("aiosqlite", "Async SQLite database"),
            ("sqlalchemy", "Database ORM"),
        ]
        
        optional_packages = [
            ("chromadb", "Vector database (optional)"),
            ("sentence_transformers", "Embeddings (optional)"),
        ]
        
        all_ok = True
        
        for package, purpose in required_packages:
            try:
                __import__(package)
                self.print_result(f"Package '{package}'", "OK", purpose)
            except ImportError:
                self.print_result(f"Package '{package}'", "ERROR", f"Missing - {purpose}")
                all_ok = False
        
        for package, purpose in optional_packages:
            try:
                __import__(package)
                self.print_result(f"Package '{package}'", "OK", purpose)
            except ImportError:
                self.print_result(f"Package '{package}'", "WARNING", f"Missing - {purpose}")
        
        if not all_ok:
            print("\n  📦 RECOMMEND: Install missing packages:")
            print("     pip install rich textual tiktoken pydantic aiohttp")
        
        return all_ok
    
    def check_opencode_installation(self) -> bool:
        """Check if OpenCode_4py is properly installed."""
        self.print_header("OpenCode_4py Installation")
        
        # Check if opencode module exists
        try:
            import opencode
            version = getattr(opencode, '__version__', 'unknown')
            self.print_result("OpenCode Module", "OK", f"v{version}")
            
            # Check key submodules
            submodules = [
                ("opencode.core.config", "Core configuration"),
                ("opencode.llmchecker.ollama", "Ollama client"),
                ("opencode.core.gpu_manager", "GPU manager"),
            ]
            
            for module, purpose in submodules:
                try:
                    __import__(module)
                    self.print_result(f"Module '{module}'", "OK", purpose)
                except ImportError as e:
                    self.print_result(f"Module '{module}'", "ERROR", str(e))
            
            return True
            
        except ImportError:
            self.print_result("OpenCode Module", "ERROR", "Not installed")
            print("\n  📦 RECOMMEND: Install OpenCode_4py:")
            print("     pip install -e .  (from source)")
            print("     or copy to python_embeded/Lib/site-packages/opencode/")
            return False
    
    def check_config_file(self) -> bool:
        """Check if configuration file exists."""
        self.print_header("Configuration")
        
        config_path = self.base_dir / "opencode.toml"
        
        if config_path.exists():
            self.print_result("Config File", "OK", str(config_path))
            return True
        else:
            self.print_result("Config File", "WARNING", "Not found at expected location")
            print(f"\n  Expected location: {config_path}")
            return True  # Not a failure, uses defaults
    
    def run_all_checks(self) -> bool:
        """Run all pre-flight checks."""
        print("\n" + "=" * 60)
        print("  OpenCode_4py Pre-flight Check")
        print("  Verifying all prerequisites...")
        print("=" * 60)
        
        # Run checks in order
        self.check_python_version()
        ollama_installed = self.check_ollama_installed()
        ollama_ok = False
        
        if ollama_installed:
            ollama_running = self.check_ollama_running()
            if ollama_running:
                ollama_ok, _ = self.check_ollama_models()
        
        # Check remote providers as alternative
        remote_ok = self.check_remote_providers()
        
        # If neither Ollama nor remote providers are available, that's an error
        if not ollama_ok and not remote_ok:
            self.print_header("AI Provider Status")
            self.print_result("AI Provider", "ERROR", "No AI providers available")
            print("\n  ❌ ERROR: OpenCode_4py requires at least one AI provider:")
            print("     Option 1: Install and run Ollama with a model")
            print("               - Install: https://ollama.ai")
            print("               - Run: ollama pull llama3.2")
            print("     Option 2: Configure a remote AI provider")
            print("               - Set OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.")
            self.errors.append(("AI Provider", "No AI providers configured"))
        
        self.check_gpu()
        self.check_dependencies()
        self.check_opencode_installation()
        self.check_config_file()
        
        # Print summary
        self.print_summary()
        
        return len(self.errors) == 0
    
    def print_summary(self) -> None:
        """Print summary of all checks."""
        print("\n" + "=" * 60)
        print("  Summary")
        print("=" * 60)
        
        print(f"\n  ✅ Passed: {len(self.successes)}")
        print(f"  ⚠️  Warnings: {len(self.warnings)}")
        print(f"  ❌ Errors: {len(self.errors)}")
        
        if self.errors:
            print("\n  Errors found:")
            for name, message in self.errors:
                print(f"    - {name}: {message}")
        
        if self.warnings:
            print("\n  Warnings:")
            for name, message in self.warnings:
                print(f"    - {name}: {message}")
        
        if not self.errors:
            print("\n  🎉 All critical checks passed! OpenCode_4py is ready to use.")
            print("\n  To start OpenCode_4py:")
            print("    - TUI mode: run_opencode_4py.bat")
            print("    - Server mode: run_opencode_4py_server.bat")
        else:
            print("\n  ⚠️  Please fix the errors above before using OpenCode_4py.")
            print("  See recommendations in each section for guidance.")


def main():
    """Main entry point."""
    checker = PreflightChecker()
    success = checker.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
