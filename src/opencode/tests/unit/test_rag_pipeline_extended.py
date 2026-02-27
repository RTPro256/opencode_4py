"""
Extended tests for RAG Pipeline.

Tests add_chunks, build_context, and other pipeline methods.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from opencode.core.rag.pipeline import RAGPipeline
from opencode.core.rag.config import RAGConfig
from opencode.core.rag.document import Document, DocumentChunk


class TestRAGPipelineChunks:
    """Tests for RAGPipeline add_chunks method."""

    @pytest.mark.asyncio
    async def test_add_chunks_basic(self):
        """Test adding pre-chunked content."""
        pipeline = RAGPipeline()
        
        # Mock embedding engine
        mock_engine = MagicMock()
        mock_engine.embed_batch = AsyncMock(return_value=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        pipeline.embedding_engine = mock_engine
        pipeline._initialized = True
        
        chunks = [
            {"text": "First chunk", "start": 0.0, "duration": 5.0},
            {"text": "Second chunk", "start": 5.0, "duration": 5.0},
        ]
        
        result = await pipeline.add_chunks(chunks, metadata={"source": "video"})
        
        assert isinstance(result, Document)
        assert len(result.chunks) == 2
        assert result.chunks[0].text == "First chunk"
        assert result.metadata["source"] == "video"

    @pytest.mark.asyncio
    async def test_add_chunks_with_start_seconds(self):
        """Test adding chunks with start seconds in metadata."""
        pipeline = RAGPipeline()
        
        mock_engine = MagicMock()
        mock_engine.embed_batch = AsyncMock(return_value=[[0.1]])
        pipeline.embedding_engine = mock_engine
        pipeline._initialized = True
        
        chunks = [{"text": "Test chunk", "start": 120.5, "duration": 10.0}]
        
        result = await pipeline.add_chunks(chunks)
        
        assert len(result.chunks) == 1
        assert result.chunks[0].metadata["start_seconds"] == 120.5
        assert result.chunks[0].metadata["duration_seconds"] == 10.0

    @pytest.mark.asyncio
    async def test_add_chunks_no_text_key(self):
        """Test adding chunks without text key."""
        pipeline = RAGPipeline()
        
        mock_engine = MagicMock()
        mock_engine.embed_batch = AsyncMock(return_value=[])
        pipeline.embedding_engine = mock_engine
        pipeline._initialized = True
        
        # Chunks without 'text' key
        chunks = [{"start": 0.0, "duration": 5.0}]
        
        result = await pipeline.add_chunks(chunks)
        
        assert isinstance(result, Document)
        assert len(result.chunks) == 1
        # Should handle empty text gracefully

    @pytest.mark.asyncio
    async def test_add_chunks_auto_initialize(self):
        """Test that add_chunks auto-initializes pipeline."""
        pipeline = RAGPipeline()
        
        # Should auto-initialize when called
        with patch("opencode.core.rag.pipeline.create_embedding_engine") as mock_create:
            mock_engine = MagicMock()
            mock_engine.embed_batch = AsyncMock(return_value=[])
            mock_create.return_value = mock_engine
            
            chunks = [{"text": "Test"}]
            await pipeline.add_chunks(chunks)
            
            # Should have called create_embedding_engine
            mock_create.assert_called_once()


class TestRAGPipelineBuildContext:
    """Tests for RAGPipeline build_context method."""

    @pytest.mark.asyncio
    async def test_build_context_with_no_engine(self):
        """Test build_context when no embedding engine."""
        pipeline = RAGPipeline()
        pipeline._initialized = True
        # No embedding engine set
        
        result = await pipeline.build_context("test query")
        
        # Should return empty string when no engine
        assert result == ""

    @pytest.mark.asyncio
    async def test_build_context_with_engine_no_results(self):
        """Test build_context with engine but no results."""
        pipeline = RAGPipeline()
        
        # Mock embedding engine that returns embedding
        mock_engine = MagicMock()
        mock_engine.embed = AsyncMock(return_value=[0.1, 0.2, 0.3])
        pipeline.embedding_engine = mock_engine
        
        # Mock query to return empty
        pipeline.query = AsyncMock(return_value=[])
        
        result = await pipeline.build_context("test query")
        
        assert result == ""


class TestRAGPipelineChunkText:
    """Tests for RAGPipeline _chunk_text method."""

    def test_chunk_text_basic(self):
        """Test basic text chunking."""
        # Use valid chunk_size (>= 50)
        pipeline = RAGPipeline(config=RAGConfig(chunk_size=50, chunk_overlap=10))
        
        text = "one two three four five six seven eight nine ten"
        chunks = pipeline._chunk_text(text)
        
        assert len(chunks) > 0
        assert isinstance(chunks[0], DocumentChunk)

    def test_chunk_text_single_word(self):
        """Test chunking single word."""
        pipeline = RAGPipeline(config=RAGConfig(chunk_size=50))
        
        text = "hello"
        chunks = pipeline._chunk_text(text)
        
        assert len(chunks) == 1

    def test_chunk_text_empty(self):
        """Test chunking empty text."""
        pipeline = RAGPipeline(config=RAGConfig(chunk_size=50))
        
        chunks = pipeline._chunk_text("")
        
        assert len(chunks) == 0

    def test_chunk_text_with_overlap(self):
        """Test chunking with overlap."""
        pipeline = RAGPipeline(config=RAGConfig(chunk_size=50, chunk_overlap=10))
        
        text = "one two three four five"
        chunks = pipeline._chunk_text(text)
        
        # Should have chunks
        assert len(chunks) > 0


class TestRAGPipelineStats:
    """Tests for RAGPipeline get_stats method."""

    def test_get_stats_basic(self):
        """Test getting pipeline stats."""
        pipeline = RAGPipeline()
        
        stats = pipeline.get_stats()
        
        assert isinstance(stats, dict)
        assert "config" in stats
        assert "retriever" in stats
        assert "initialized" in stats

    def test_get_stats_initialized(self):
        """Test stats when initialized."""
        pipeline = RAGPipeline()
        pipeline._initialized = True
        
        stats = pipeline.get_stats()
        
        assert stats["initialized"] is True


class TestRAGPipelineClear:
    """Tests for RAGPipeline clear method."""

    def test_clear_documents(self):
        """Test clearing all documents."""
        pipeline = RAGPipeline()
        
        # Clear should work without error
        pipeline.clear()
        
        # Just verify it doesn't raise
        assert True
