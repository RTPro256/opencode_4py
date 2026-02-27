"""
HuggingFace Research Agent

Search and download models from HuggingFace Hub.
Based on Locally-Hosted-LM-Research-Assistant implementation.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import huggingface_hub
try:
    from huggingface_hub import HfApi, hf_hub_download, list_models
    HUGGINGFACE_AVAILABLE = True
except ImportError:
    HUGGINGFACE_AVAILABLE = False
    HfApi = None
    hf_hub_download = None
    list_models = None


class ModelInfo(BaseModel):
    """Information about a HuggingFace model"""
    model_id: str = Field(..., description="Model ID (e.g., 'bert-base-uncased')")
    author: str = Field("", description="Model author/organization")
    downloads: int = Field(0, description="Number of downloads")
    likes: int = Field(0, description="Number of likes")
    tags: List[str] = Field(default_factory=list, description="Model tags")
    pipeline_tag: Optional[str] = Field(None, description="Pipeline tag (e.g., 'text-generation')")
    library_name: Optional[str] = Field(None, description="Library name (e.g., 'transformers')")
    created_at: Optional[str] = Field(None, description="Creation date")
    last_modified: Optional[str] = Field(None, description="Last modified date")
    card_data: Dict[str, Any] = Field(default_factory=dict, description="Model card data")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "model_id": self.model_id,
            "author": self.author,
            "downloads": self.downloads,
            "likes": self.likes,
            "tags": self.tags,
            "pipeline_tag": self.pipeline_tag,
            "library_name": self.library_name,
            "created_at": self.created_at,
            "last_modified": self.last_modified,
            "card_data": self.card_data,
        }


class HuggingFaceAgent:
    """
    Search and download models from HuggingFace Hub.
    
    Features:
    - Model search with filters
    - Model download
    - Model info retrieval
    - Dataset search
    """
    
    def __init__(
        self,
        cache_dir: Optional[str] = None,
        token: Optional[str] = None,
    ):
        """
        Initialize the HuggingFace agent.
        
        Args:
            cache_dir: Directory to cache downloaded models
            token: HuggingFace API token
        """
        if not HUGGINGFACE_AVAILABLE:
            raise ImportError(
                "huggingface_hub not installed. Install with: pip install huggingface_hub"
            )
        
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.token = token or os.environ.get("HUGGINGFACE_TOKEN")
        self.api = HfApi(token=self.token)
    
    def search_models(
        self,
        query: str,
        limit: int = 10,
        filter_tags: Optional[List[str]] = None,
        sort: str = "downloads",
    ) -> List[ModelInfo]:
        """
        Search for models on HuggingFace Hub.
        
        Args:
            query: Search query
            limit: Maximum number of results
            filter_tags: Tags to filter by
            sort: Sort criterion (downloads, likes, lastModified)
            
        Returns:
            List of ModelInfo objects
        """
        try:
            models = list_models(
                search=query,
                limit=limit,
                filter=filter_tags,
                sort=sort,
                token=self.token,
            )
            
            results = []
            for model in models:
                info = ModelInfo(
                    model_id=model.id,
                    author=model.author or "",
                    downloads=model.downloads or 0,
                    likes=model.likes or 0,
                    tags=list(model.tags) if model.tags else [],
                    pipeline_tag=model.pipeline_tag,
                    library_name=model.library_name,
                    created_at=str(model.created_at) if model.created_at else None,
                    last_modified=str(model.last_modified) if model.last_modified else None,
                    card_data=model.card_data if model.card_data else {},
                )
                results.append(info)
            
            logger.info(f"Found {len(results)} models for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Model search failed: {e}")
            return []
    
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """
        Get detailed information about a model.
        
        Args:
            model_id: Model ID (e.g., 'bert-base-uncased')
            
        Returns:
            ModelInfo or None if not found
        """
        try:
            model_info = self.api.model_info(model_id, token=self.token)
            
            return ModelInfo(
                model_id=model_info.id,
                author=model_info.author or "",
                downloads=model_info.downloads or 0,
                likes=model_info.likes or 0,
                tags=list(model_info.tags) if model_info.tags else [],
                pipeline_tag=model_info.pipeline_tag,
                library_name=model_info.library_name,
                created_at=str(model_info.created_at) if model_info.created_at else None,
                last_modified=str(model_info.last_modified) if model_info.last_modified else None,
                card_data=model_info.card_data if model_info.card_data else {},
            )
            
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return None
    
    def download_model(
        self,
        model_id: str,
        filename: Optional[str] = None,
        local_dir: Optional[str] = None,
    ) -> Optional[Path]:
        """
        Download a model from HuggingFace Hub.
        
        Args:
            model_id: Model ID
            filename: Specific file to download (if None, downloads all)
            local_dir: Local directory to save to
            
        Returns:
            Path to downloaded file/directory or None on failure
        """
        try:
            local_dir = local_dir or (self.cache_dir / model_id.replace("/", "_"))
            
            if filename:
                path = hf_hub_download(
                    repo_id=model_id,
                    filename=filename,
                    local_dir=str(local_dir),
                    token=self.token,
                )
            else:
                # Download all files
                from huggingface_hub import snapshot_download
                path = snapshot_download(
                    repo_id=model_id,
                    local_dir=str(local_dir),
                    token=self.token,
                )
            
            logger.info(f"Downloaded model to: {path}")
            return Path(path)
            
        except Exception as e:
            logger.error(f"Model download failed: {e}")
            return None
    
    def list_model_files(self, model_id: str) -> List[str]:
        """
        List files in a model repository.
        
        Args:
            model_id: Model ID
            
        Returns:
            List of file paths
        """
        try:
            files = self.api.list_repo_files(model_id, token=self.token)
            return list(files)
        except Exception as e:
            logger.error(f"Failed to list model files: {e}")
            return []
    
    def search_datasets(
        self,
        query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search for datasets on HuggingFace Hub.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of dataset info dictionaries
        """
        try:
            from huggingface_hub import list_datasets
            
            datasets = list_datasets(
                search=query,
                limit=limit,
                token=self.token,
            )
            
            results = []
            for ds in datasets:
                results.append({
                    "id": ds.id,
                    "author": ds.author,
                    "downloads": ds.downloads,
                    "likes": ds.likes,
                    "tags": list(ds.tags) if ds.tags else [],
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Dataset search failed: {e}")
            return []
