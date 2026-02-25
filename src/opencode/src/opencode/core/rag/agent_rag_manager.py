"""Agent RAG Manager

Simplified RAG management for agent-specific retrieval.

File Structure:
    RAG/
    ├── agent_{name}/              # RAG for specific agent
    │   ├── RAG/                   # Holds RAG files
    │   │   ├── {agent_name}-RAG/  # Generated RAG index
    │   │   ├── README-RAG.md      # Information about the RAG
    │   │   └── {source_files}/    # Files used to generate RAG
    │   └── config.json            # Agent RAG configuration
"""

import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AgentRAGConfig:
    """Configuration for an agent's RAG."""
    agent: str
    description: str = ""
    embedding_model: str = "nomic-embed-text"
    embedding_provider: str = "ollama"
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k: int = 5
    min_similarity: float = 0.7
    sources: List[str] = field(default_factory=list)
    file_patterns: List[str] = field(default_factory=lambda: ["*.py", "*.md", "*.txt"])
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    document_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent": self.agent,
            "description": self.description,
            "embedding_model": self.embedding_model,
            "embedding_provider": self.embedding_provider,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "top_k": self.top_k,
            "min_similarity": self.min_similarity,
            "sources": self.sources,
            "file_patterns": self.file_patterns,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "document_count": self.document_count,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentRAGConfig":
        """Create from dictionary."""
        return cls(
            agent=data.get("agent", "unknown"),
            description=data.get("description", ""),
            embedding_model=data.get("embedding_model", "nomic-embed-text"),
            embedding_provider=data.get("embedding_provider", "ollama"),
            chunk_size=data.get("chunk_size", 512),
            chunk_overlap=data.get("chunk_overlap", 50),
            top_k=data.get("top_k", 5),
            min_similarity=data.get("min_similarity", 0.7),
            sources=data.get("sources", []),
            file_patterns=data.get("file_patterns", ["*.py", "*.md", "*.txt"]),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            document_count=data.get("document_count", 0),
        )


class AgentRAGManager:
    """
    Manages agent-specific RAG indexes.
    
    This provides a simplified interface for creating, querying, and
    managing RAG indexes for specific agents.
    
    Usage:
        manager = AgentRAGManager()
        
        # Create RAG for an agent
        await manager.create_rag("code", sources=["./src"])
        
        # Query an agent's RAG
        results = await manager.query("code", "How to implement auth?")
        
        # Add files to existing RAG
        await manager.add_files("code", ["./new_module.py"])
    """
    
    def __init__(self, rag_root: Optional[Path] = None):
        """
        Initialize the agent RAG manager.
        
        Args:
            rag_root: Root directory for RAG files. Defaults to ./RAG
        """
        self.rag_root = rag_root or Path.cwd() / "RAG"
        self._ensure_structure()
    
    def _ensure_structure(self) -> None:
        """Ensure the RAG directory structure exists."""
        self.rag_root.mkdir(parents=True, exist_ok=True)
    
    def _get_agent_dir(self, agent: str) -> Path:
        """Get the directory for an agent's RAG."""
        return self.rag_root / f"agent_{agent}"
    
    def _get_rag_dir(self, agent: str) -> Path:
        """Get the RAG directory for an agent."""
        return self._get_agent_dir(agent) / "RAG"
    
    def _get_config_path(self, agent: str) -> Path:
        """Get the config file path for an agent."""
        return self._get_agent_dir(agent) / "config.json"
    
    def _get_index_path(self, agent: str) -> Path:
        """Get the index directory path for an agent."""
        return self._get_rag_dir(agent) / f"{agent}-RAG"
    
    def agent_exists(self, agent: str) -> bool:
        """Check if an agent has a RAG configured."""
        return self._get_config_path(agent).exists()
    
    def list_agents(self) -> List[str]:
        """List all agents with RAG configured."""
        agents = []
        for path in self.rag_root.iterdir():
            if path.is_dir() and path.name.startswith("agent_"):
                agent_name = path.name.replace("agent_", "")
                if self._get_config_path(agent_name).exists():
                    agents.append(agent_name)
        return sorted(agents)
    
    def load_config(self, agent: str) -> Optional[AgentRAGConfig]:
        """Load configuration for an agent's RAG."""
        config_path = self._get_config_path(agent)
        if not config_path.exists():
            return None
        
        try:
            with open(config_path, "r") as f:
                data = json.load(f)
            return AgentRAGConfig.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load config for agent {agent}: {e}")
            return None
    
    def save_config(self, config: AgentRAGConfig) -> None:
        """Save configuration for an agent's RAG."""
        config_path = self._get_config_path(config.agent)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, "w") as f:
            json.dump(config.to_dict(), f, indent=2)
    
    async def create_rag(
        self,
        agent: str,
        sources: Optional[List[str]] = None,
        description: str = "",
        embedding_model: str = "nomic-embed-text",
        chunk_size: int = 512,
    ) -> AgentRAGConfig:
        """
        Create a RAG for an agent.
        
        Args:
            agent: Agent name (e.g., "code", "architect")
            sources: List of source paths to index
            description: Description of the RAG
            embedding_model: Model to use for embeddings
            chunk_size: Size of text chunks
            
        Returns:
            The created configuration
        """
        # Create directory structure
        agent_dir = self._get_agent_dir(agent)
        rag_dir = self._get_rag_dir(agent)
        index_dir = self._get_index_path(agent)
        
        agent_dir.mkdir(parents=True, exist_ok=True)
        rag_dir.mkdir(parents=True, exist_ok=True)
        index_dir.mkdir(parents=True, exist_ok=True)
        
        # Create config
        config = AgentRAGConfig(
            agent=agent,
            description=description,
            embedding_model=embedding_model,
            chunk_size=chunk_size,
            sources=sources or [],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        self.save_config(config)
        
        # Create README
        await self._create_readme(agent, config)
        
        # Index sources if provided
        if sources:
            await self._index_sources(agent, sources, config)
        
        logger.info(f"Created RAG for agent '{agent}'")
        return config
    
    async def _create_readme(self, agent: str, config: AgentRAGConfig) -> None:
        """Create README for an agent's RAG."""
        readme_path = self._get_rag_dir(agent) / "README-RAG.md"
        
        content = f"""# {agent.title()} Agent RAG

This RAG (Retrieval-Augmented Generation) index is for the **{agent}** agent.

## Purpose

{config.description or f'The {agent} agent uses this RAG for context-aware responses.'}

## Configuration

- **Embedding Model**: {config.embedding_model}
- **Chunk Size**: {config.chunk_size}
- **Top K**: {config.top_k}
- **Min Similarity**: {config.min_similarity}

## Usage

```bash
# Query this RAG
opencode rag query --agent {agent} "your query"

# Add files
opencode rag add --agent {agent} ./path/to/files

# Rebuild index
opencode rag rebuild --agent {agent}
```

## Status

- **Created**: {config.created_at or 'Unknown'}
- **Documents**: {config.document_count}
- **Last Updated**: {config.updated_at or 'Never'}
"""
        
        with open(readme_path, "w") as f:
            f.write(content)
    
    async def _index_sources(
        self,
        agent: str,
        sources: List[str],
        config: AgentRAGConfig,
    ) -> int:
        """Index source files for an agent's RAG."""
        # Copy source files to RAG directory
        rag_dir = self._get_rag_dir(agent)
        total_docs = 0
        
        for source in sources:
            source_path = Path(source)
            if not source_path.exists():
                logger.warning(f"Source path does not exist: {source}")
                continue
            
            if source_path.is_file():
                # Copy single file
                dest = rag_dir / source_path.name
                shutil.copy2(source_path, dest)
                total_docs += 1
            elif source_path.is_dir():
                # Copy directory
                dest = rag_dir / source_path.name
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(source_path, dest)
                
                # Count files
                for pattern in config.file_patterns:
                    total_docs += len(list(dest.glob(f"**/{pattern}")))
        
        # Update config
        config.document_count = total_docs
        config.updated_at = datetime.now().isoformat()
        self.save_config(config)
        
        return total_docs
    
    async def add_files(
        self,
        agent: str,
        files: List[str],
    ) -> int:
        """
        Add files to an agent's RAG.
        
        Args:
            agent: Agent name
            files: List of file paths to add
            
        Returns:
            Number of files added
        """
        config = self.load_config(agent)
        if not config:
            raise ValueError(f"No RAG found for agent '{agent}'")
        
        added = await self._index_sources(agent, files, config)
        logger.info(f"Added {added} files to agent '{agent}' RAG")
        return added
    
    async def query(
        self,
        agent: str,
        query: str,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query an agent's RAG.
        
        Args:
            agent: Agent name
            query: Search query
            top_k: Number of results (uses config default if not specified)
            
        Returns:
            List of matching documents with content and metadata
        """
        config = self.load_config(agent)
        if not config:
            raise ValueError(f"No RAG found for agent '{agent}'")
        
        rag_dir = self._get_rag_dir(agent)
        index_dir = self._get_index_path(agent)
        
        # For now, do a simple file search
        # In production, this would use the RAG pipeline with embeddings
        results = []
        k = top_k or config.top_k
        
        # Search through source files
        for pattern in config.file_patterns:
            for file_path in rag_dir.glob(f"**/{pattern}"):
                if file_path.name == "README-RAG.md":
                    continue
                
                try:
                    content = file_path.read_text(encoding="utf-8")
                    
                    # Simple text matching (would be vector similarity in production)
                    if query.lower() in content.lower():
                        # Find context around match
                        idx = content.lower().find(query.lower())
                        start = max(0, idx - 200)
                        end = min(len(content), idx + len(query) + 200)
                        context = content[start:end]
                        
                        results.append({
                            "file": str(file_path.relative_to(rag_dir)),
                            "content": context,
                            "score": 1.0,  # Would be similarity score
                            "metadata": {
                                "source": file_path.name,
                                "size": len(content),
                            },
                        })
                        
                        if len(results) >= k:
                            return results
                except Exception as e:
                    logger.warning(f"Error reading file {file_path}: {e}")
        
        return results
    
    async def delete_rag(self, agent: str) -> bool:
        """
        Delete an agent's RAG.
        
        Args:
            agent: Agent name
            
        Returns:
            True if deleted, False if not found
        """
        agent_dir = self._get_agent_dir(agent)
        if not agent_dir.exists():
            return False
        
        shutil.rmtree(agent_dir)
        logger.info(f"Deleted RAG for agent '{agent}'")
        return True
    
    def get_status(self, agent: str) -> Dict[str, Any]:
        """Get status of an agent's RAG."""
        config = self.load_config(agent)
        if not config:
            return {
                "exists": False,
                "agent": agent,
            }
        
        index_dir = self._get_index_path(agent)
        
        return {
            "exists": True,
            "agent": agent,
            "description": config.description,
            "document_count": config.document_count,
            "embedding_model": config.embedding_model,
            "created_at": config.created_at,
            "updated_at": config.updated_at,
            "index_exists": index_dir.exists(),
            "sources": config.sources,
        }
