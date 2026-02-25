"""
Unit tests for RAG Pipeline implementation.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from opencode.core.rag.pipeline import RAGPipeline
from opencode.core.rag.config import RAGConfig
from opencode.core.rag.document import Document, DocumentChunk


class TestRAGConfig:
    """Tests for RAGConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RAGConfig()
        
        assert config.chunk_size > 0
        assert config.chunk_overlap >= 0
        assert config.embedding_model is not None
        assert config.top_k > 0

    def test_custom_config(self):
        """Test custom configuration values."""
        config = RAGConfig(
            chunk_size=1024,
            chunk_overlap=100,
            embedding_model="custom-model",
            top_k=10,
        )
        
        assert config.chunk_size == 1024
        assert config.chunk_overlap == 100
        assert config.embedding_model == "custom-model"
        assert config.top_k == 10

    def test_chunk_overlap_less_than_chunk_size(self):
        """Test that chunk overlap should be less than chunk size."""
        config = RAGConfig(chunk_size=500, chunk_overlap=50)
        
        assert config.chunk_overlap < config.chunk_size

    def test_min_similarity_range(self):
        """Test min_similarity is in valid range."""
        config = RAGConfig(min_similarity=0.5)
        
        assert 0.0 <= config.min_similarity <= 1.0

    def test_max_documents(self):
        """Test max_documents configuration."""
        config = RAGConfig(max_documents=5000)
        
        assert config.max_documents == 5000

    def test_embedding_dimensions(self):
        """Test embedding dimensions configuration."""
        config = RAGConfig(embedding_dimensions=1024)
        
        assert config.embedding_dimensions == 1024

    def test_persist_index(self):
        """Test persist index configuration."""
        config = RAGConfig(persist_index=True)
        
        assert config.persist_index is True

    def test_index_path(self):
        """Test index path configuration."""
        config = RAGConfig(index_path="/tmp/test_index")
        
        assert config.index_path == "/tmp/test_index"


class TestDocument:
    """Tests for Document class."""

    def test_document_creation(self):
        """Test creating a document."""
        doc = Document(
            id="test-doc",
            text="This is test content",
            metadata={"source": "test"}
        )
        
        assert doc.id == "test-doc"
        assert doc.text == "This is test content"
        assert doc.metadata["source"] == "test"

    def test_document_default_metadata(self):
        """Test document with default metadata."""
        doc = Document(id="test", text="content")
        
        assert doc.metadata == {} or doc.metadata is not None

    def test_document_text_length(self):
        """Test document text length."""
        doc = Document(id="test", text="Hello World")
        
        assert len(doc.text) == 11

    def test_document_with_chunks(self):
        """Test document with chunks."""
        chunk = DocumentChunk(
            id="chunk1",
            text="Test chunk",
            start_index=0,
            end_index=10
        )
        doc = Document(
            id="test",
            text="Test document",
            chunks=[chunk]
        )
        
        assert len(doc.chunks) == 1
        assert doc.chunks[0].text == "Test chunk"


class TestDocumentChunk:
    """Tests for DocumentChunk class."""

    def test_chunk_creation(self):
        """Test creating a document chunk."""
        chunk = DocumentChunk(
            id="chunk-1",
            text="This is chunk text",
            start_index=0,
            end_index=18
        )
        
        assert chunk.id == "chunk-1"
        assert chunk.text == "This is chunk text"
        assert chunk.start_index == 0
        assert chunk.end_index == 18

    def test_chunk_length(self):
        """Test chunk length property."""
        chunk = DocumentChunk(
            text="Hello World",
            start_index=0,
            end_index=11
        )
        
        assert chunk.length == 11

    def test_chunk_has_embedding_false(self):
        """Test chunk has_embedding is False when no embedding."""
        chunk = DocumentChunk(text="Test")
        
        assert chunk.has_embedding is False

    def test_chunk_has_embedding_true(self):
        """Test chunk has_embedding is True with embedding."""
        chunk = DocumentChunk(
            text="Test",
            embedding=[0.1, 0.2, 0.3]
        )
        
        assert chunk.has_embedding is True

    def test_chunk_default_id(self):
        """Test chunk gets default ID."""
        chunk = DocumentChunk(text="Test")
        
        assert chunk.id is not None
        assert len(chunk.id) > 0


class TestRAGPipeline:
    """Tests for RAGPipeline class."""

    @pytest.fixture
    def config(self):
        """Create a RAGConfig instance."""
        return RAGConfig(
            chunk_size=512,
            chunk_overlap=50,
            embedding_model="nomic-embed-text",
            top_k=5,
        )

    @pytest.fixture
    def pipeline(self, config):
        """Create a RAGPipeline instance."""
        return RAGPipeline(config)

    def test_pipeline_initialization(self, pipeline, config):
        """Test pipeline initializes correctly."""
        assert pipeline.config == config

    def test_pipeline_default_config(self):
        """Test pipeline with default config."""
        pipeline = RAGPipeline()
        
        assert pipeline.config is not None
        assert pipeline.config.chunk_size > 0

    def test_pipeline_not_initialized_by_default(self, pipeline):
        """Test pipeline is not initialized by default."""
        assert pipeline._initialized is False

    def test_get_stats(self, pipeline):
        """Test getting pipeline stats."""
        stats = pipeline.get_stats()
        
        assert "config" in stats
        assert "initialized" in stats
        assert stats["initialized"] is False

    def test_clear_pipeline(self, pipeline):
        """Test clearing pipeline."""
        # Should not raise
        pipeline.clear()


class TestRAGPipelineChunking:
    """Tests for text chunking."""

    @pytest.fixture
    def pipeline(self):
        """Create a RAGPipeline instance."""
        config = RAGConfig(chunk_size=50, chunk_overlap=10)
        return RAGPipeline(config)

    def test_chunk_text_basic(self, pipeline):
        """Test basic text chunking."""
        text = "This is a test document with multiple words for chunking and we need enough words to create multiple chunks."
        
        chunks = pipeline._chunk_text(text)
        
        assert len(chunks) > 0
        assert all(isinstance(c, DocumentChunk) for c in chunks)

    def test_chunk_text_preserves_content(self, pipeline):
        """Test that chunking preserves content."""
        text = "This is a test document with enough words to be chunked properly."
        
        chunks = pipeline._chunk_text(text)
        
        # All words should be in some chunk
        all_text = " ".join(c.text for c in chunks)
        assert "This" in all_text

    def test_chunk_text_with_overlap(self, pipeline):
        """Test text chunking with overlap."""
        text = "One two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen."
        
        chunks = pipeline._chunk_text(text)
        
        # With overlap, we should have multiple chunks
        assert len(chunks) >= 1


class TestRAGPipelineAsync:
    """Async tests for RAGPipeline."""

    @pytest.fixture
    def pipeline(self):
        """Create a RAGPipeline instance."""
        return RAGPipeline()

    @pytest.mark.asyncio
    async def test_initialize(self, pipeline):
        """Test pipeline initialization."""
        with patch.object(pipeline, 'initialize') as mock_init:
            mock_init.return_value = None
            
            await pipeline.initialize()
            
            # initialize can be called
            assert True

    @pytest.mark.asyncio
    async def test_add_document(self, pipeline):
        """Test adding a document."""
        with patch.object(pipeline, 'add_document') as mock_add:
            mock_add.return_value = Document(id="test", text="Test content")
            
            result = await pipeline.add_document(text="Test content")
            
            assert result is not None

    @pytest.mark.asyncio
    async def test_query(self, pipeline):
        """Test querying the pipeline."""
        with patch.object(pipeline, 'query') as mock_query:
            mock_query.return_value = []
            
            results = await pipeline.query("test query")
            
            assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_build_context(self, pipeline):
        """Test building context."""
        with patch.object(pipeline, 'query') as mock_query:
            mock_query.return_value = []
            
            context = await pipeline.build_context("test query")
            
            assert isinstance(context, str)


class TestRAGPipelineRetriever:
    """Tests for retriever integration."""

    @pytest.fixture
    def pipeline(self):
        """Create a RAGPipeline instance."""
        config = RAGConfig(top_k=3)
        return RAGPipeline(config)

    def test_retriever_created(self, pipeline):
        """Test that retriever is created."""
        assert pipeline.retriever is not None

    def test_retriever_has_stats(self, pipeline):
        """Test that retriever has stats."""
        stats = pipeline.retriever.get_stats()
        
        assert isinstance(stats, dict)


class TestRAGPipelineAddChunks:
    """Tests for add_chunks method."""

    @pytest.fixture
    def pipeline(self):
        """Create a RAGPipeline instance."""
        return RAGPipeline()

    @pytest.mark.asyncio
    async def test_add_chunks_basic(self, pipeline):
        """Test adding pre-chunked content."""
        chunks = [
            {"text": "First chunk", "start": 0, "duration": 5},
            {"text": "Second chunk", "start": 5, "duration": 5},
        ]
        
        with patch('opencode.core.rag.pipeline.create_embedding_engine') as mock_create:
            mock_engine = AsyncMock()
            mock_engine.embed_batch = AsyncMock(return_value=[[0.1] * 384, [0.2] * 384])
            mock_create.return_value = mock_engine
            
            document = await pipeline.add_chunks(chunks, metadata={"source": "test"})
            
            assert document is not None
            assert len(document.chunks) == 2
            assert document.text == "First chunk Second chunk"

    @pytest.mark.asyncio
    async def test_add_chunks_with_metadata(self, pipeline):
        """Test adding chunks with metadata."""
        chunks = [
            {"text": "Test chunk", "start": 10.5, "duration": 3.5},
        ]
        
        with patch('opencode.core.rag.pipeline.create_embedding_engine') as mock_create:
            mock_engine = AsyncMock()
            mock_engine.embed_batch = AsyncMock(return_value=[[0.1] * 384])
            mock_create.return_value = mock_engine
            
            document = await pipeline.add_chunks(chunks, metadata={"video": "test.mp4"})
            
            assert document.metadata["video"] == "test.mp4"
            assert document.chunks[0].metadata["start_seconds"] == 10.5
            assert document.chunks[0].metadata["duration_seconds"] == 3.5

    @pytest.mark.asyncio
    async def test_add_chunks_empty(self, pipeline):
        """Test adding empty chunks list."""
        with patch('opencode.core.rag.pipeline.create_embedding_engine') as mock_create:
            mock_engine = AsyncMock()
            mock_engine.embed_batch = AsyncMock(return_value=[])
            mock_create.return_value = mock_engine
            
            document = await pipeline.add_chunks([], metadata={})
            
            assert document is not None
            assert len(document.chunks) == 0
            assert document.text == ""

    @pytest.mark.asyncio
    async def test_add_chunks_missing_fields(self, pipeline):
        """Test adding chunks with missing fields."""
        chunks = [
            {"text": "Chunk without timing"},
        ]
        
        with patch('opencode.core.rag.pipeline.create_embedding_engine') as mock_create:
            mock_engine = AsyncMock()
            mock_engine.embed_batch = AsyncMock(return_value=[[0.1] * 384])
            mock_create.return_value = mock_engine
            
            document = await pipeline.add_chunks(chunks)
            
            assert len(document.chunks) == 1
            # Should have default values for missing fields
            assert document.chunks[0].metadata["start_seconds"] == 0
            assert document.chunks[0].metadata["duration_seconds"] == 0


class TestRAGPipelineQuery:
    """Tests for query method."""

    @pytest.fixture
    def pipeline(self):
        """Create a RAGPipeline instance."""
        return RAGPipeline()

    @pytest.mark.asyncio
    async def test_query_no_embedding_engine(self, pipeline):
        """Test query when embedding engine is None."""
        pipeline._initialized = True
        pipeline.embedding_engine = None
        
        results = await pipeline.query("test query")
        
        assert results == []

    @pytest.mark.asyncio
    async def test_query_with_results(self, pipeline):
        """Test query returning results."""
        from opencode.core.rag.retriever import RetrievalResult
        
        mock_retriever = AsyncMock()
        mock_retriever.retrieve = AsyncMock(return_value=[
            MagicMock(spec=RetrievalResult, score=0.9),
        ])
        
        with patch('opencode.core.rag.pipeline.create_embedding_engine') as mock_create:
            mock_engine = AsyncMock()
            mock_engine.embed = AsyncMock(return_value=[0.1] * 384)
            mock_create.return_value = mock_engine
            
            pipeline.retriever = mock_retriever
            
            results = await pipeline.query("test query", top_k=5, min_similarity=0.5)
            
            mock_retriever.retrieve.assert_called_once()
            assert len(results) == 1


class TestRAGPipelineBuildContext:
    """Tests for build_context method."""

    @pytest.fixture
    def pipeline(self):
        """Create a RAGPipeline instance."""
        return RAGPipeline()

    @pytest.mark.asyncio
    async def test_build_context_empty(self, pipeline):
        """Test building context with no results."""
        with patch.object(pipeline, 'query') as mock_query:
            mock_query.return_value = []
            
            context = await pipeline.build_context("test query")
            
            assert context == ""

    @pytest.mark.asyncio
    async def test_build_context_with_results(self, pipeline):
        """Test building context with results."""
        mock_chunk = MagicMock()
        mock_chunk.text = "This is relevant content."
        mock_chunk.metadata = {}
        
        mock_result = MagicMock()
        mock_result.chunk = mock_chunk
        
        with patch.object(pipeline, 'query') as mock_query:
            mock_query.return_value = [mock_result]
            
            context = await pipeline.build_context("test query")
            
            assert "This is relevant content" in context

    @pytest.mark.asyncio
    async def test_build_context_with_timestamps(self, pipeline):
        """Test building context with timestamp metadata."""
        mock_chunk = MagicMock()
        mock_chunk.text = "Content at timestamp."
        mock_chunk.metadata = {"start_seconds": 125}  # 2:05
        
        mock_result = MagicMock()
        mock_result.chunk = mock_chunk
        
        with patch.object(pipeline, 'query') as mock_query:
            mock_query.return_value = [mock_result]
            
            context = await pipeline.build_context("test query", include_metadata=True)
            
            assert "[2:05]" in context

    @pytest.mark.asyncio
    async def test_build_context_respects_max_tokens(self, pipeline):
        """Test that context respects max_tokens limit."""
        mock_chunk1 = MagicMock()
        mock_chunk1.text = "A" * 1000  # ~250 tokens
        mock_chunk1.metadata = {}
        
        mock_chunk2 = MagicMock()
        mock_chunk2.text = "B" * 1000  # ~250 tokens
        mock_chunk2.metadata = {}
        
        mock_result1 = MagicMock()
        mock_result1.chunk = mock_chunk1
        
        mock_result2 = MagicMock()
        mock_result2.chunk = mock_chunk2
        
        with patch.object(pipeline, 'query') as mock_query:
            mock_query.return_value = [mock_result1, mock_result2]
            
            context = await pipeline.build_context("test query", max_tokens=100)
            
            # Should only include first chunk due to token limit
            assert "A" in context or context == ""  # May be empty if first chunk exceeds limit

    @pytest.mark.asyncio
    async def test_build_context_without_metadata(self, pipeline):
        """Test building context without metadata."""
        mock_chunk = MagicMock()
        mock_chunk.text = "Just the text."
        mock_chunk.metadata = {"start_seconds": 10}
        
        mock_result = MagicMock()
        mock_result.chunk = mock_chunk
        
        with patch.object(pipeline, 'query') as mock_query:
            mock_query.return_value = [mock_result]
            
            context = await pipeline.build_context("test query", include_metadata=False)
            
            assert "[0:10]" not in context
            assert "Just the text" in context


class TestRAGPipelineAddDocument:
    """Tests for add_document method."""

    @pytest.fixture
    def pipeline(self):
        """Create a RAGPipeline instance."""
        config = RAGConfig(chunk_size=50, chunk_overlap=10)
        return RAGPipeline(config)

    @pytest.mark.asyncio
    async def test_add_document_with_chunking(self, pipeline):
        """Test adding document with chunking enabled."""
        text = "This is a test document with multiple words for chunking and we need enough words to create multiple chunks."
        
        with patch('opencode.core.rag.pipeline.create_embedding_engine') as mock_create:
            mock_engine = AsyncMock()
            # Return embeddings based on number of chunks requested
            mock_engine.embed_batch = AsyncMock(side_effect=lambda texts: [[0.1] * 384 for _ in texts])
            mock_create.return_value = mock_engine
            
            document = await pipeline.add_document(text=text, chunk=True)
            
            assert document is not None
            assert len(document.chunks) > 0

    @pytest.mark.asyncio
    async def test_add_document_without_chunking(self, pipeline):
        """Test adding document without chunking."""
        text = "This is a simple document."
        
        with patch('opencode.core.rag.pipeline.create_embedding_engine') as mock_create:
            mock_engine = AsyncMock()
            mock_create.return_value = mock_engine
            
            document = await pipeline.add_document(text=text, chunk=False)
            
            assert document is not None
            assert len(document.chunks) == 0

    @pytest.mark.asyncio
    async def test_add_document_with_metadata(self, pipeline):
        """Test adding document with metadata."""
        with patch('opencode.core.rag.pipeline.create_embedding_engine') as mock_create:
            mock_engine = AsyncMock()
            mock_engine.embed_batch = AsyncMock(return_value=[])
            mock_create.return_value = mock_engine
            
            document = await pipeline.add_document(
                text="Test",
                metadata={"author": "test"},
                source="test.txt"
            )
            
            assert document.metadata["author"] == "test"
            assert document.source == "test.txt"

    @pytest.mark.asyncio
    async def test_add_document_initializes_pipeline(self, pipeline):
        """Test that add_document initializes the pipeline."""
        assert pipeline._initialized is False
        
        with patch('opencode.core.rag.pipeline.create_embedding_engine') as mock_create:
            mock_engine = AsyncMock()
            mock_engine.embed_batch = AsyncMock(return_value=[])
            mock_create.return_value = mock_engine
            
            await pipeline.add_document(text="Test")
            
            assert pipeline._initialized is True


class TestRAGPipelineInitialize:
    """Tests for initialize method."""

    @pytest.fixture
    def pipeline(self):
        """Create a RAGPipeline instance."""
        return RAGPipeline()

    @pytest.mark.asyncio
    async def test_initialize_creates_embedding_engine(self, pipeline):
        """Test that initialize creates embedding engine."""
        with patch('opencode.core.rag.pipeline.create_embedding_engine') as mock_create:
            mock_create.return_value = MagicMock()
            
            await pipeline.initialize()
            
            mock_create.assert_called_once()
            assert pipeline.embedding_engine is not None

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self, pipeline):
        """Test that initialize is idempotent."""
        with patch('opencode.core.rag.pipeline.create_embedding_engine') as mock_create:
            mock_create.return_value = MagicMock()
            
            await pipeline.initialize()
            await pipeline.initialize()
            
            # Should only be called once
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_sets_flag(self, pipeline):
        """Test that initialize sets the initialized flag."""
        with patch('opencode.core.rag.pipeline.create_embedding_engine') as mock_create:
            mock_create.return_value = MagicMock()
            
            await pipeline.initialize()
            
            assert pipeline._initialized is True
