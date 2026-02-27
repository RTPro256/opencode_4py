"""
Ollama API client for LLM Checker.

Provides async HTTP client for communicating with Ollama server.
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Optional, AsyncGenerator, Any

import httpx

from .models import (
    OllamaModel,
    OllamaResponse,
    OllamaRunningModel,
    OllamaVersion,
    OllamaPullProgress,
)


class OllamaClient:
    """Async HTTP client for Ollama API.
    
    Provides methods for:
    - Checking Ollama availability
    - Listing and managing models
    - Running inference
    - Pulling/deleting models
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """Initialize Ollama client.
        
        Args:
            base_url: Ollama server URL. Defaults to OLLAMA_HOST env var
                      or http://localhost:11434.
        """
        # Support OLLAMA_HOST environment variable
        self.base_url = base_url or os.environ.get(
            "OLLAMA_HOST", 
            os.environ.get("OLLAMA_URL", "http://localhost:11434")
        )
        
        # Normalize URL
        if not self.base_url.startswith(("http://", "https://")):
            self.base_url = f"http://{self.base_url}"
        self.base_url = self.base_url.rstrip("/")
        
        # Cache
        self._is_available: Optional[dict] = None
        self._last_check: float = 0
        self._cache_timeout: float = 30.0  # 30 seconds
        self._pending_check: Optional[asyncio.Future] = None
    
    async def check_availability(self, force: bool = False) -> dict:
        """Check if Ollama is available.
        
        Args:
            force: Force a fresh check.
            
        Returns:
            Dictionary with 'available', 'version', and optional 'error'.
        """
        import time
        current_time = time.time()
        
        # Use cache if valid
        if not force and self._is_available is not None:
            if current_time - self._last_check < self._cache_timeout:
                return self._is_available
        
        # Prevent concurrent checks
        if self._pending_check is not None:
            return await self._pending_check
        
        # Create future for concurrent requests
        loop = asyncio.get_event_loop()
        self._pending_check = loop.create_future()
        
        try:
            result = await self._do_availability_check()
            self._is_available = result
            self._last_check = current_time
            self._pending_check.set_result(result)
            return result
        except Exception as e:
            result = {"available": False, "error": str(e)}
            self._is_available = result
            self._last_check = current_time
            self._pending_check.set_result(result)
            return result
        finally:
            self._pending_check = None
    
    async def _do_availability_check(self) -> dict:
        """Perform the actual availability check."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/version")
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "available": True,
                        "version": data.get("version", "unknown"),
                    }
                else:
                    return {
                        "available": False,
                        "error": f"HTTP {response.status_code}",
                    }
        except httpx.ConnectError:
            return {
                "available": False,
                "error": f"Cannot connect to Ollama at {self.base_url}",
                "hint": "Make sure Ollama is running. Try: ollama serve",
            }
        except httpx.TimeoutException:
            return {
                "available": False,
                "error": f"Connection timeout at {self.base_url}",
                "hint": "Ollama is not responding. Check if it's running.",
            }
        except Exception as e:
            return {
                "available": False,
                "error": str(e),
            }
    
    async def get_version(self) -> Optional[OllamaVersion]:
        """Get Ollama version information.
        
        Returns:
            OllamaVersion or None if unavailable.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/version")
                
                if response.status_code == 200:
                    data = response.json()
                    return OllamaVersion(version=data.get("version", "unknown"))
        except Exception:
            pass
        return None
    
    async def list_models(self) -> list[OllamaModel]:
        """List all downloaded models.
        
        Returns:
            List of OllamaModel objects.
        """
        availability = await self.check_availability()
        if not availability.get("available"):
            raise ConnectionError(f"Ollama not available: {availability.get('error')}")
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                
                if response.status_code != 200:
                    raise RuntimeError(f"HTTP {response.status_code}: {response.text}")
                
                data = response.json()
                models = []
                
                for model_data in data.get("models", []):
                    model = self._parse_model(model_data)
                    models.append(model)
                
                return models
        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to list models: {e}")
    
    async def get_running_models(self) -> list[OllamaRunningModel]:
        """Get currently running models.
        
        Returns:
            List of OllamaRunningModel objects.
        """
        availability = await self.check_availability()
        if not availability.get("available"):
            return []
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/ps")
                
                if response.status_code != 200:
                    return []
                
                data = response.json()
                models = []
                
                for model_data in data.get("models", []):
                    model = self._parse_running_model(model_data)
                    models.append(model)
                
                return models
        except Exception:
            return []
    
    async def pull_model(
        self, 
        model: str,
        stream: bool = True
    ) -> AsyncGenerator[OllamaPullProgress, None]:
        """Pull a model from Ollama registry or Hugging Face.
        
        Supports:
        - Ollama registry: "llama3.2:3b"
        - Hugging Face: "hf.co/{username}/{repository}" or "hf.co/{username}/{repository}:{quantization}"
        
        Args:
            model: Model name to pull.
            stream: Whether to stream progress.
            
        Yields:
            OllamaPullProgress objects.
        """
        # Normalize Hugging Face model names
        model = self._normalize_model_name(model)
        
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/pull",
                json={"name": model, "stream": stream},
            ) as response:
                if response.status_code != 200:
                    raise RuntimeError(f"Failed to pull model: {response.text}")
                
                async for line in response.aiter_lines():
                    if not line.strip():
                        continue
                    
                    try:
                        data = json.loads(line)
                        progress = OllamaPullProgress(
                            status=data.get("status", ""),
                            digest=data.get("digest", ""),
                            total=data.get("total", 0),
                            completed=data.get("completed", 0),
                        )
                        yield progress
                    except json.JSONDecodeError:
                        continue
    
    def _normalize_model_name(self, model: str) -> str:
        """Normalize model name for Ollama.
        
        Handles Hugging Face model names:
        - hf.co/{username}/{repository} -> hf.co/{username}/{repository}
        - hf.co/{username}/{repository}:{quantization} -> hf.co/{username}/{repository}:{quantization}
        
        Args:
            model: Model name.
            
        Returns:
            Normalized model name.
        """
        # Check if it's a Hugging Face model
        if model.startswith("hf.co/"):
            # Already in correct format
            return model
        
        # Check for huggingface.co/ prefix
        if model.startswith("huggingface.co/"):
            return model.replace("huggingface.co/", "hf.co/")
        
        # Check for @ prefix (alternative HF format)
        if model.startswith("@"):
            # @username/repo -> hf.co/username/repo
            return "hf.co/" + model[1:]
        
        return model
    
    def is_huggingface_model(self, model: str) -> bool:
        """Check if a model is from Hugging Face.
        
        Args:
            model: Model name.
            
        Returns:
            True if the model is from Hugging Face.
        """
        return (
            model.startswith("hf.co/") or 
            model.startswith("huggingface.co/") or
            model.startswith("@")
        )
    
    def parse_huggingface_model(self, model: str) -> dict:
        """Parse Hugging Face model name into components.
        
        Args:
            model: Model name like "hf.co/{username}/{repository}:{quantization}".
            
        Returns:
            Dictionary with 'username', 'repository', 'quantization' (optional).
        """
        normalized = self._normalize_model_name(model)
        
        if not normalized.startswith("hf.co/"):
            return {}
        
        # Remove hf.co/ prefix
        parts = normalized[6:].split("/")
        
        if len(parts) < 2:
            return {}
        
        username = parts[0]
        repo_parts = parts[1].split(":")
        repository = repo_parts[0]
        quantization = repo_parts[1] if len(repo_parts) > 1 else None
        
        return {
            "username": username,
            "repository": repository,
            "quantization": quantization,
            "full_name": f"{username}/{repository}",
            "model_name": normalized,
        }
    
    async def pull_huggingface_model(
        self,
        username: str,
        repository: str,
        quantization: Optional[str] = None,
        stream: bool = True,
    ) -> AsyncGenerator[OllamaPullProgress, None]:
        """Pull a model from Hugging Face.
        
        Args:
            username: Hugging Face username/organization.
            repository: Model repository name.
            quantization: Optional quantization (e.g., "Q4_K_M").
            stream: Whether to stream progress.
            
        Yields:
            OllamaPullProgress objects.
        """
        model = f"hf.co/{username}/{repository}"
        if quantization:
            model += f":{quantization}"
        
        async for progress in self.pull_model(model, stream):
            yield progress
    
    async def delete_model(self, model: str) -> bool:
        """Delete a model.
        
        Args:
            model: Model name to delete.
            
        Returns:
            True if successful.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(
                    "DELETE",
                    f"{self.base_url}/api/delete",
                    json={"name": model},
                )
                
                return response.status_code == 200
        except Exception:
            return False
    
    async def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        context: Optional[list[int]] = None,
        stream: bool = False,
        raw: bool = False,
        format: Optional[str] = None,
        options: Optional[dict] = None,
    ) -> OllamaResponse:
        """Generate a response from a model.
        
        Args:
            model: Model name.
            prompt: Input prompt.
            system: System prompt.
            context: Context from previous generation.
            stream: Whether to stream response.
            raw: Return raw response.
            format: Output format (e.g., "json").
            options: Additional model options.
            
        Returns:
            OllamaResponse object.
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
        }
        
        if system:
            payload["system"] = system
        if context:
            payload["context"] = context
        if raw:
            payload["raw"] = raw
        if format:
            payload["format"] = format
        if options:
            payload["options"] = options
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Generation failed: {response.text}")
            
            data = response.json()
            return self._parse_response(data)
    
    async def chat(
        self,
        model: str,
        messages: list[dict],
        stream: bool = False,
        format: Optional[str] = None,
        options: Optional[dict] = None,
    ) -> OllamaResponse:
        """Chat with a model.
        
        Args:
            model: Model name.
            messages: List of message dicts with 'role' and 'content'.
            stream: Whether to stream response.
            format: Output format (e.g., "json").
            options: Additional model options.
            
        Returns:
            OllamaResponse object.
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
        }
        
        if format:
            payload["format"] = format
        if options:
            payload["options"] = options
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Chat failed: {response.text}")
            
            data = response.json()
            
            # Parse chat response
            message = data.get("message", {})
            return OllamaResponse(
                model=model,
                content=message.get("content", ""),
                done=data.get("done", True),
                total_duration=data.get("total_duration", 0),
                load_duration=data.get("load_duration", 0),
                prompt_eval_count=data.get("prompt_eval_count", 0),
                prompt_eval_duration=data.get("prompt_eval_duration", 0),
                eval_count=data.get("eval_count", 0),
                eval_duration=data.get("eval_duration", 0),
            )
    
    async def embed(
        self,
        model: str,
        input: str | list[str],
        options: Optional[dict] = None,
    ) -> list[float] | list[list[float]]:
        """Generate embeddings for input text.
        
        Args:
            model: Model name.
            input: Input text or list of texts.
            options: Additional model options.
            
        Returns:
            Embedding vector(s).
        """
        payload = {
            "model": model,
            "input": input,
        }
        
        if options:
            payload["options"] = options
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/embed",
                json=payload,
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"Embedding failed: {response.text}")
            
            data = response.json()
            return data.get("embeddings", [])
    
    async def show_model(self, model: str) -> dict:
        """Get detailed information about a model.
        
        Args:
            model: Model name.
            
        Returns:
            Dictionary with model details.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/show",
                    json={"name": model},
                )
                
                if response.status_code != 200:
                    raise RuntimeError(f"Failed to get model info: {response.text}")
                
                return response.json()
        except Exception as e:
            raise RuntimeError(f"Failed to get model info: {e}")
    
    def _parse_model(self, data: dict) -> OllamaModel:
        """Parse model data from API response."""
        # Parse modified_at
        modified_at = None
        if "modified_at" in data:
            try:
                # Parse ISO format datetime
                modified_at = datetime.fromisoformat(
                    data["modified_at"].replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                pass
        
        return OllamaModel(
            name=data.get("name", ""),
            size=data.get("size", 0),
            digest=data.get("digest", ""),
            modified_at=modified_at,
            details=data.get("details", {}),
        )
    
    def _parse_running_model(self, data: dict) -> OllamaRunningModel:
        """Parse running model data from API response."""
        expires_at = None
        if "expires_at" in data:
            try:
                expires_at = datetime.fromisoformat(
                    data["expires_at"].replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                pass
        
        return OllamaRunningModel(
            name=data.get("name", ""),
            model=data.get("model", ""),
            size=data.get("size", 0),
            digest=data.get("digest", ""),
            details=data.get("details", {}),
            expires_at=expires_at,
            size_vram=data.get("size_vram", 0),
        )
    
    def _parse_response(self, data: dict) -> OllamaResponse:
        """Parse generate response from API."""
        return OllamaResponse(
            model=data.get("model", ""),
            content=data.get("response", ""),
            done=data.get("done", True),
            total_duration=data.get("total_duration", 0),
            load_duration=data.get("load_duration", 0),
            prompt_eval_count=data.get("prompt_eval_count", 0),
            prompt_eval_duration=data.get("prompt_eval_duration", 0),
            eval_count=data.get("eval_count", 0),
            eval_duration=data.get("eval_duration", 0),
        )
    
    async def test_connection(self) -> dict:
        """Test connection to Ollama and return diagnostic info.
        
        Returns:
            Dictionary with connection status and details.
        """
        result = await self.check_availability(force=True)
        
        if result.get("available"):
            try:
                models = await self.list_models()
                result["models_found"] = len(models)
                result["models"] = [m.name for m in models]
            except Exception as e:
                result["models_error"] = str(e)
        
        return result
