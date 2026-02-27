"""
Model Manager.

Manages local LLM models - downloading, caching, and inference.
Inspired by igllama's CLI commands (pull, list, run, etc.).
"""

import json
import logging
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import httpx
from pydantic import BaseModel

from .config import (
    ChatTemplateType,
    GGUFMetadata,
    LLMConfig,
    ModelConfig,
    ModelSource,
    SamplingConfig,
)

logger = logging.getLogger(__name__)


class ModelStatus(str, Enum):
    """Model availability status."""
    READY = "ready"
    DOWNLOADING = "downloading"
    ERROR = "error"
    NOT_FOUND = "not_found"


@dataclass
class ModelInfo:
    """Information about a local model."""
    
    name: str
    path: Path
    size: int
    status: ModelStatus
    metadata: Optional[GGUFMetadata] = None
    source: ModelSource = ModelSource.LOCAL
    downloaded_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "path": str(self.path),
            "size": self.size,
            "size_formatted": self._format_size(self.size),
            "status": self.status.value,
            "source": self.source.value,
            "metadata": self.metadata.model_dump() if self.metadata else None,
            "downloaded_at": self.downloaded_at.isoformat() if self.downloaded_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
        }
    
    @staticmethod
    def _format_size(size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"


class ModelManager:
    """
    Manages local LLM models.
    
    Provides functionality similar to igllama:
    - List available models
    - Download models from HuggingFace
    - Inspect GGUF metadata
    - Remove models
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize the model manager.
        
        Args:
            config: LLM configuration. Creates default if not provided.
        """
        self.config = config or LLMConfig()
        self._models_cache: Dict[str, ModelInfo] = {}
        self._models_dir = self.config.models_dir
        self._models_dir.mkdir(parents=True, exist_ok=True)
        
        # Load cached models
        self._load_cache()
    
    def _load_cache(self) -> None:
        """Load cached model information."""
        cache_file = self._models_dir / ".model_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    cache_data = json.load(f)
                    for name, info in cache_data.items():
                        self._models_cache[name] = ModelInfo(
                            name=info["name"],
                            path=Path(info["path"]),
                            size=info["size"],
                            status=ModelStatus(info["status"]),
                            source=ModelSource(info.get("source", "local")),
                            metadata=GGUFMetadata(**info["metadata"]) if info.get("metadata") else None,
                            downloaded_at=datetime.fromisoformat(info["downloaded_at"]) if info.get("downloaded_at") else None,
                            last_used=datetime.fromisoformat(info["last_used"]) if info.get("last_used") else None,
                        )
            except Exception as e:
                logger.warning(f"Failed to load model cache: {e}")
    
    def _save_cache(self) -> None:
        """Save model cache to disk."""
        cache_file = self._models_dir / ".model_cache.json"
        cache_data = {name: info.to_dict() for name, info in self._models_cache.items()}
        try:
            with open(cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save model cache: {e}")
    
    def list_models(self) -> List[ModelInfo]:
        """
        List all available local models.
        
        Returns:
            List of ModelInfo objects.
        """
        models = []
        
        # Scan models directory
        if self._models_dir.exists():
            for gguf_file in self._models_dir.glob("*.gguf"):
                name = gguf_file.stem
                if name not in self._models_cache:
                    # New model found - create info
                    size = gguf_file.stat().st_size
                    info = ModelInfo(
                        name=name,
                        path=gguf_file,
                        size=size,
                        status=ModelStatus.READY,
                        source=ModelSource.LOCAL,
                    )
                    self._models_cache[name] = info
        
        models = list(self._models_cache.values())
        return sorted(models, key=lambda m: m.name)
    
    def get_model(self, name: str) -> Optional[ModelInfo]:
        """
        Get model by name.
        
        Args:
            name: Model name or alias.
            
        Returns:
            ModelInfo if found, None otherwise.
        """
        # Check aliases
        if name in self.config.aliases:
            name = self.config.aliases[name]
        
        # Check cache
        if name in self._models_cache:
            return self._models_cache[name]
        
        # Check file system
        model_path = self._models_dir / f"{name}.gguf"
        if model_path.exists():
            size = model_path.stat().st_size
            info = ModelInfo(
                name=name,
                path=model_path,
                size=size,
                status=ModelStatus.READY,
                source=ModelSource.LOCAL,
            )
            self._models_cache[name] = info
            return info
        
        return None
    
    async def pull_model(
        self,
        model_id: str,
        filename: Optional[str] = None,
        progress_callback: Optional[callable] = None,
    ) -> ModelInfo:
        """
        Download a model from HuggingFace.
        
        Args:
            model_id: HuggingFace model ID (e.g., "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF")
            filename: Specific file to download. Auto-detects if not provided.
            progress_callback: Optional callback for progress updates.
            
        Returns:
            ModelInfo for the downloaded model.
        """
        logger.info(f"Pulling model: {model_id}")
        
        # Get model info from HuggingFace
        api_url = f"https://huggingface.co/api/models/{model_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(api_url)
            response.raise_for_status()
            model_data = response.json()
            
            # Find GGUF file
            if not filename:
                siblings = model_data.get("siblings", [])
                for f in siblings:
                    if f.get("rfilename", "").endswith(".gguf"):
                        filename = f["rfilename"]
                        break
                
                if not filename:
                    raise ValueError(f"No GGUF file found for model: {model_id}")
            
            # Download file
            download_url = f"https://huggingface.co/{model_id}/resolve/main/{filename}"
            output_path = self._models_dir / filename
            
            # Create temp file for download
            temp_path = output_path.with_suffix(".tmp")
            
            async with httpx.AsyncClient(follow_redirects=True) as download_client:
                async with download_client.stream("GET", download_url) as response:
                    response.raise_for_status()
                    total_size = int(response.headers.get("content-length", 0))
                    
                    downloaded = 0
                    with open(temp_path, "wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if progress_callback and total_size:
                                progress_callback(downloaded, total_size)
            
            # Move to final location
            temp_path.rename(output_path)
            
            # Create model info
            info = ModelInfo(
                name=output_path.stem,
                path=output_path,
                size=output_path.stat().st_size,
                status=ModelStatus.READY,
                source=ModelSource.HUGGINGFACE,
                downloaded_at=datetime.now(),
            )
            
            self._models_cache[info.name] = info
            self._save_cache()
            
            logger.info(f"Model downloaded: {info.name}")
            return info
    
    def inspect_model(self, name: str) -> Optional[GGUFMetadata]:
        """
        Inspect GGUF model metadata.
        
        Args:
            name: Model name.
            
        Returns:
            GGUFMetadata if successful, None otherwise.
        """
        model = self.get_model(name)
        if not model:
            return None
        
        try:
            metadata = GGUFMetadata.from_gguf_file(model.path)
            return metadata
        except Exception as e:
            logger.error(f"Failed to inspect model: {e}")
            return None
    
    def remove_model(self, name: str) -> bool:
        """
        Remove a model from the cache and disk.
        
        Args:
            name: Model name.
            
        Returns:
            True if successful, False otherwise.
        """
        model = self.get_model(name)
        if not model:
            return False
        
        try:
            # Remove file
            if model.path.exists():
                model.path.unlink()
            
            # Remove from cache
            del self._models_cache[name]
            self._save_cache()
            
            logger.info(f"Model removed: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove model: {e}")
            return False
    
    def get_model_path(self, name: str) -> Optional[Path]:
        """
        Get the full path to a model file.
        
        Args:
            name: Model name or alias.
            
        Returns:
            Path to model file if found.
        """
        model = self.get_model(name)
        return model.path if model else None
    
    def update_last_used(self, name: str) -> None:
        """
        Update the last used timestamp for a model.
        
        Args:
            name: Model name.
        """
        model = self.get_model(name)
        if model:
            model.last_used = datetime.now()
            self._save_cache()


# Default model manager instance
_default_manager: Optional[ModelManager] = None


def get_model_manager(config: Optional[LLMConfig] = None) -> ModelManager:
    """
    Get the default model manager instance.
    
    Args:
        config: Optional configuration override.
        
    Returns:
        ModelManager instance.
    """
    global _default_manager
    if _default_manager is None or config is not None:
        _default_manager = ModelManager(config)
    return _default_manager
