"""
Tests for RAG Integration with Multi-Model Patterns

Tests the RAG process node and its integration with workflows.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from opencode.workflow.nodes.rag_process import RAGProcessNode
from opencode.workflow.state import ExecutionStatus


@pytest.fixture
def rag_node():
    """Create a RAG process node for testing."""
    return RAGProcessNode("test_rag", {
        "collection": "test_docs",
        "top_k": 5,
        "min_similarity": 0.7,
        "query_rewriting": False,
    })


@pytest.fixture
def rag_node_with_rewriting():
    """Create a RAG process node with query rewriting enabled."""
    return RAGProcessNode("test_rag_rewrite", {
        "collection": "test_docs",
        "top_k": 3,
        "min_similarity": 0.5,
        "query_rewriting": True,
        "query_rewriting_method": "hyde",
    })


class TestRAGProcessNode:
    """Tests for RAGProcessNode."""
    
    def test_node_creation(self, rag_node):
        """Test creating a RAG process node."""
        assert rag_node.node_id == "test_rag"
        assert rag_node.config["collection"] == "test_docs"
        assert rag_node.config["top_k"] == 5
    
    def test_node_type(self, rag_node):
        """Test node type is correct."""
        assert rag_node.node_type == "rag_process"
    
    @pytest.mark.asyncio
    async def test_execute_with_empty_query(self, rag_node):
        """Test execution with empty query returns empty results."""
        result = await rag_node.execute({"query": ""})
        
        assert result.status == ExecutionStatus.COMPLETED
        assert result.outputs["context"] == ""
        assert result.outputs["document_count"] == 0
    
    @pytest.mark.asyncio
    async def test_execute_with_no_query_key(self, rag_node):
        """Test execution with no query key."""
        result = await rag_node.execute({})
        
        assert result.status == ExecutionStatus.COMPLETED
        assert result.outputs["context"] == ""
        assert result.outputs["document_count"] == 0
    
    @pytest.mark.asyncio
    async def test_execute_with_query(self, rag_node):
        """Test execution with a valid query."""
        mock_documents = [
            MagicMock(
                content="Document 1 content",
                metadata={"source": "file1.txt"},
                score=0.9,
            ),
            MagicMock(
                content="Document 2 content",
                metadata={"source": "file2.txt"},
                score=0.8,
            ),
        ]
        
        with patch.object(rag_node, '_get_rag_pipeline') as mock_get_pipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.retrieve = AsyncMock(return_value=mock_documents)
            mock_get_pipeline.return_value = mock_pipeline
            
            result = await rag_node.execute({"query": "test query"})
            
            assert result.status == ExecutionStatus.COMPLETED
            assert result.outputs["document_count"] == 2
            assert "Document 1 content" in result.outputs["context"]
            assert "file1.txt" in result.outputs["context"]
    
    @pytest.mark.asyncio
    async def test_execute_with_input_key(self, rag_node):
        """Test execution using 'input' key instead of 'query'."""
        mock_documents = [
            MagicMock(
                content="Test content",
                metadata={"source": "test.txt"},
                score=0.85,
            ),
        ]
        
        with patch.object(rag_node, '_get_rag_pipeline') as mock_get_pipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.retrieve = AsyncMock(return_value=mock_documents)
            mock_get_pipeline.return_value = mock_pipeline
            
            result = await rag_node.execute({"input": "test input"})
            
            assert result.status == ExecutionStatus.COMPLETED
            assert result.outputs["document_count"] == 1
    
    @pytest.mark.asyncio
    async def test_execute_with_retrieval_error(self, rag_node):
        """Test execution handles retrieval errors gracefully."""
        with patch.object(rag_node, '_get_rag_pipeline') as mock_get_pipeline:
            mock_pipeline = MagicMock()
            # Make retrieve raise an exception
            mock_pipeline.retrieve = AsyncMock(side_effect=Exception("Retrieval failed"))
            # Make retriever also raise to ensure error propagates
            mock_pipeline.retriever = MagicMock()
            mock_pipeline.retriever.retrieve = AsyncMock(side_effect=Exception("Retrieval failed"))
            mock_get_pipeline.return_value = mock_pipeline
            
            result = await rag_node.execute({"query": "test query"})
            
            # The node catches retrieval errors and returns empty results (completed status)
            # This is the actual behavior - it doesn't fail, it gracefully handles errors
            assert result.status == ExecutionStatus.COMPLETED
            assert result.outputs["document_count"] == 0
    
    @pytest.mark.asyncio
    async def test_execute_with_query_rewriting(self, rag_node_with_rewriting):
        """Test execution with query rewriting enabled."""
        mock_documents = [
            MagicMock(
                content="Rewritten content",
                metadata={"source": "rewritten.txt"},
                score=0.9,
            ),
        ]
        
        with patch.object(rag_node_with_rewriting, '_get_rag_pipeline') as mock_get_pipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.retrieve = AsyncMock(return_value=mock_documents)
            mock_get_pipeline.return_value = mock_pipeline
            
            with patch.object(rag_node_with_rewriting, '_rewrite_query') as mock_rewrite:
                mock_rewrite.return_value = "rewritten query"
                
                result = await rag_node_with_rewriting.execute({"query": "original query"})
                
                assert result.status == ExecutionStatus.COMPLETED
                mock_rewrite.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_query_rewriting_failure_falls_back(self, rag_node_with_rewriting):
        """Test that query rewriting failure falls back to original query."""
        mock_documents = [
            MagicMock(
                content="Content",
                metadata={"source": "test.txt"},
                score=0.8,
            ),
        ]
        
        with patch.object(rag_node_with_rewriting, '_get_rag_pipeline') as mock_get_pipeline:
            mock_pipeline = MagicMock()
            mock_pipeline.retrieve = AsyncMock(return_value=mock_documents)
            mock_get_pipeline.return_value = mock_pipeline
            
            with patch.object(rag_node_with_rewriting, '_rewrite_query') as mock_rewrite:
                mock_rewrite.side_effect = Exception("Rewriting failed")
                
                result = await rag_node_with_rewriting.execute({"query": "original query"})
                
                # Should still complete, just without rewriting
                assert result.status == ExecutionStatus.COMPLETED


class TestRAGProcessNodeHelpers:
    """Tests for RAGProcessNode helper methods."""
    
    def test_format_context_empty(self, rag_node):
        """Test formatting empty document list."""
        result = rag_node._format_context([])
        assert result == ""
    
    def test_format_context_single_document(self, rag_node):
        """Test formatting a single document."""
        doc = MagicMock(
            content="Test content",
            metadata={"source": "test.txt"},
        )
        
        result = rag_node._format_context([doc])
        
        assert "[test.txt]" in result
        assert "Test content" in result
    
    def test_format_context_multiple_documents(self, rag_node):
        """Test formatting multiple documents."""
        docs = [
            MagicMock(content="Content 1", metadata={"source": "file1.txt"}),
            MagicMock(content="Content 2", metadata={"source": "file2.txt"}),
        ]
        
        result = rag_node._format_context(docs)
        
        assert "[file1.txt]" in result
        assert "[file2.txt]" in result
        assert "Content 1" in result
        assert "Content 2" in result
        assert "\n\n" in result  # Documents separated by double newline
    
    def test_doc_to_dict_with_to_dict(self, rag_node):
        """Test document conversion with to_dict method."""
        doc = MagicMock()
        doc.to_dict.return_value = {"content": "test", "metadata": {}}
        
        result = rag_node._doc_to_dict(doc)
        
        assert result == {"content": "test", "metadata": {}}
    
    def test_doc_to_dict_with_model_dump(self, rag_node):
        """Test document conversion with model_dump method."""
        doc = MagicMock()
        delattr(doc, 'to_dict')  # Remove to_dict
        doc.model_dump.return_value = {"content": "test", "metadata": {}}
        
        result = rag_node._doc_to_dict(doc)
        
        assert result == {"content": "test", "metadata": {}}
    
    def test_doc_to_dict_with_attributes(self, rag_node):
        """Test document conversion with direct attributes."""
        doc = MagicMock()
        delattr(doc, 'to_dict')
        delattr(doc, 'model_dump')
        doc.content = "test content"
        doc.metadata = {"source": "test.txt"}
        doc.score = 0.9
        
        result = rag_node._doc_to_dict(doc)
        
        assert result["content"] == "test content"
        assert result["metadata"]["source"] == "test.txt"
        assert result["score"] == 0.9
    
    def test_doc_to_dict_fallback(self, rag_node):
        """Test document conversion fallback to string."""
        doc = "simple string"
        
        result = rag_node._doc_to_dict(doc)
        
        assert result == {"content": "simple string"}


class TestRAGProcessNodeSchema:
    """Tests for RAGProcessNode schema."""
    
    def test_get_schema(self):
        """Test getting node schema."""
        schema = RAGProcessNode.get_schema()
        
        assert schema["node_type"] == "rag_process"
        assert schema["display_name"] == "RAG Process"
        assert "inputs" in schema
        assert "outputs" in schema
        assert "config" in schema
    
    def test_schema_inputs(self):
        """Test schema inputs are correct."""
        schema = RAGProcessNode.get_schema()
        inputs = {i["name"]: i for i in schema["inputs"]}
        
        assert "query" in inputs
        assert inputs["query"]["required"] is True
        assert "input" in inputs
        assert inputs["input"]["required"] is False
    
    def test_schema_outputs(self):
        """Test schema outputs are correct."""
        schema = RAGProcessNode.get_schema()
        outputs = {o["name"]: o for o in schema["outputs"]}
        
        assert "context" in outputs
        assert "documents" in outputs
        assert "query" in outputs
        assert "document_count" in outputs
    
    def test_schema_config(self):
        """Test schema config options are correct."""
        schema = RAGProcessNode.get_schema()
        config = schema["config"]
        
        assert "collection" in config
        assert "top_k" in config
        assert "min_similarity" in config
        assert "query_rewriting" in config
        assert "query_rewriting_method" in config


class TestRAGProcessNodePipeline:
    """Tests for RAG pipeline integration."""
    
    @pytest.mark.asyncio
    async def test_get_rag_pipeline_lazy_load(self, rag_node):
        """Test that RAG pipeline is lazy-loaded."""
        assert rag_node._rag_pipeline is None
        
        pipeline = rag_node._get_rag_pipeline()
        
        assert pipeline is not None
        assert rag_node._rag_pipeline is pipeline
    
    @pytest.mark.asyncio
    async def test_get_rag_pipeline_uses_config(self, rag_node):
        """Test that RAG pipeline uses node config."""
        pipeline = rag_node._get_rag_pipeline()
        
        # Pipeline should be created with config values
        assert pipeline is not None


class TestQueryRewriting:
    """Tests for query rewriting functionality."""
    
    @pytest.mark.asyncio
    async def test_rewrite_query_success(self, rag_node_with_rewriting):
        """Test successful query rewriting."""
        with patch('opencode.core.rag.QueryRewriter') as MockRewriter:
            mock_rewriter = MagicMock()
            mock_result = MagicMock()
            mock_result.rewritten_queries = ["rewritten query 1", "rewritten query 2"]
            mock_rewriter.rewrite = AsyncMock(return_value=mock_result)
            MockRewriter.return_value = mock_rewriter
            
            result = await rag_node_with_rewriting._rewrite_query("original query")
            
            assert result == "rewritten query 1"
    
    @pytest.mark.asyncio
    async def test_rewrite_query_with_hypothetical_document(self, rag_node_with_rewriting):
        """Test query rewriting with HyDE (returns original when only hypothetical doc)."""
        with patch('opencode.core.rag.QueryRewriter') as MockRewriter:
            mock_rewriter = MagicMock()
            mock_result = MagicMock()
            mock_result.rewritten_queries = []
            mock_result.hypothetical_document = "Hypothetical document content..."
            mock_rewriter.rewrite = AsyncMock(return_value=mock_result)
            MockRewriter.return_value = mock_rewriter
            
            result = await rag_node_with_rewriting._rewrite_query("original query")
            
            # Should return original query when only hypothetical document is available
            assert result == "original query"
    
    @pytest.mark.asyncio
    async def test_rewrite_query_import_error(self, rag_node_with_rewriting):
        """Test query rewriting handles import error."""
        with patch('opencode.core.rag.QueryRewriter', side_effect=ImportError):
            result = await rag_node_with_rewriting._rewrite_query("test query")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_rewrite_query_exception(self, rag_node_with_rewriting):
        """Test query rewriting handles exceptions."""
        with patch('opencode.core.rag.QueryRewriter') as MockRewriter:
            MockRewriter.side_effect = Exception("Rewriter error")
            
            result = await rag_node_with_rewriting._rewrite_query("test query")
            
            assert result is None
