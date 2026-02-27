"""Tests for YouTube Chunking module."""

import pytest
from unittest.mock import MagicMock

from opencode.core.youtube.chunking import (
    ChunkingStrategy,
    ChunkingConfig,
    ChunkedTranscript,
    TranscriptChunker,
)
from opencode.core.youtube.transcript import TranscriptChunk, VideoTranscript


class TestChunkingStrategy:
    """Tests for ChunkingStrategy enum."""
    
    def test_values(self):
        """Test enum values."""
        assert ChunkingStrategy.FIXED_SIZE == "fixed_size"
        assert ChunkingStrategy.TIME_BASED == "time_based"
        assert ChunkingStrategy.SENTENCE == "sentence"
        assert ChunkingStrategy.SEMANTIC == "semantic"


class TestChunkingConfig:
    """Tests for ChunkingConfig."""
    
    def test_default_values(self):
        """Test default values."""
        config = ChunkingConfig()
        assert config.strategy == ChunkingStrategy.FIXED_SIZE
        assert config.chunk_size == 10
        assert config.target_duration == 30.0
        assert config.overlap == 0
        assert config.min_chunk_size == 1
        assert config.max_chunk_size == 20
    
    def test_custom_values(self):
        """Test custom values."""
        config = ChunkingConfig(
            strategy=ChunkingStrategy.TIME_BASED,
            chunk_size=5,
            target_duration=60.0,
            overlap=2,
            min_chunk_size=2,
            max_chunk_size=15
        )
        assert config.strategy == ChunkingStrategy.TIME_BASED
        assert config.chunk_size == 5
        assert config.target_duration == 60.0
        assert config.overlap == 2


class TestChunkedTranscript:
    """Tests for ChunkedTranscript."""
    
    def test_custom_values(self):
        """Test custom values."""
        chunk = ChunkedTranscript(
            text="Hello world",
            start=0.0,
            duration=10.0,
            end=10.0,
            video_id="abc123",
            chunk_index=0,
            original_chunks=2,
            metadata={"strategy": "fixed_size"}
        )
        assert chunk.text == "Hello world"
        assert chunk.start == 0.0
        assert chunk.duration == 10.0
        assert chunk.end == 10.0
        assert chunk.video_id == "abc123"
        assert chunk.chunk_index == 0
        assert chunk.original_chunks == 2
    
    def test_to_dict(self):
        """Test to_dict method."""
        chunk = ChunkedTranscript(
            text="Hello world",
            start=0.0,
            duration=10.0,
            end=10.0,
            video_id="abc123",
            chunk_index=0,
            original_chunks=2,
            metadata={"strategy": "fixed_size"}
        )
        d = chunk.to_dict()
        
        assert d["text"] == "Hello world"
        assert d["start"] == 0.0
        assert d["duration"] == 10.0
        assert d["end"] == 10.0
        assert d["video_id"] == "abc123"
        assert d["chunk_index"] == 0
        assert d["original_chunks"] == 2
        assert d["metadata"]["strategy"] == "fixed_size"


class TestTranscriptChunker:
    """Tests for TranscriptChunker."""
    
    def test_init(self):
        """Test initialization."""
        chunker = TranscriptChunker()
        assert chunker.config is not None
        assert chunker.config.strategy == ChunkingStrategy.FIXED_SIZE
    
    def test_init_with_config(self):
        """Test initialization with config."""
        config = ChunkingConfig(strategy=ChunkingStrategy.TIME_BASED)
        chunker = TranscriptChunker(config)
        assert chunker.config.strategy == ChunkingStrategy.TIME_BASED
    
    def test_chunk_empty_transcript(self):
        """Test chunking empty transcript."""
        chunker = TranscriptChunker()
        transcript = VideoTranscript(video_id="abc123")
        
        result = chunker.chunk(transcript)
        assert result == []
    
    def test_chunk_fixed_size(self):
        """Test fixed size chunking."""
        config = ChunkingConfig(strategy=ChunkingStrategy.FIXED_SIZE, chunk_size=2)
        chunker = TranscriptChunker(config)
        
        chunks = [
            TranscriptChunk(text="Hello", start=0.0, duration=5.0),
            TranscriptChunk(text="world", start=5.0, duration=5.0),
            TranscriptChunk(text="foo", start=10.0, duration=5.0),
            TranscriptChunk(text="bar", start=15.0, duration=5.0),
        ]
        transcript = VideoTranscript(video_id="abc123", chunks=chunks)
        
        result = chunker.chunk(transcript)
        
        assert len(result) == 2
        assert result[0].text == "Hello world"
        assert result[0].start == 0.0
        assert result[0].original_chunks == 2
        assert result[1].text == "foo bar"
        assert result[1].start == 10.0
    
    def test_chunk_fixed_size_with_overlap(self):
        """Test fixed size chunking with overlap."""
        config = ChunkingConfig(
            strategy=ChunkingStrategy.FIXED_SIZE,
            chunk_size=3,
            overlap=1
        )
        chunker = TranscriptChunker(config)
        
        chunks = [
            TranscriptChunk(text="A", start=0.0, duration=1.0),
            TranscriptChunk(text="B", start=1.0, duration=1.0),
            TranscriptChunk(text="C", start=2.0, duration=1.0),
            TranscriptChunk(text="D", start=3.0, duration=1.0),
            TranscriptChunk(text="E", start=4.0, duration=1.0),
        ]
        transcript = VideoTranscript(video_id="abc123", chunks=chunks)
        
        result = chunker.chunk(transcript)
        
        # With overlap=1, step is chunk_size - overlap = 2
        # First chunk: A, B, C (indices 0-2)
        # Second chunk: C, D, E (indices 2-4) - but we only have D, E left
        assert len(result) >= 1
    
    def test_chunk_time_based(self):
        """Test time-based chunking."""
        config = ChunkingConfig(strategy=ChunkingStrategy.TIME_BASED, target_duration=10.0)
        chunker = TranscriptChunker(config)
        
        chunks = [
            TranscriptChunk(text="A", start=0.0, duration=5.0),
            TranscriptChunk(text="B", start=5.0, duration=5.0),
            TranscriptChunk(text="C", start=10.0, duration=5.0),
            TranscriptChunk(text="D", start=15.0, duration=5.0),
        ]
        transcript = VideoTranscript(video_id="abc123", chunks=chunks)
        
        result = chunker.chunk(transcript)
        
        # Each pair should be 10 seconds
        assert len(result) == 2
        assert result[0].duration == 10.0
        assert result[1].duration == 10.0
    
    def test_chunk_time_based_remaining(self):
        """Test time-based chunking with remaining chunks."""
        config = ChunkingConfig(strategy=ChunkingStrategy.TIME_BASED, target_duration=10.0)
        chunker = TranscriptChunker(config)
        
        chunks = [
            TranscriptChunk(text="A", start=0.0, duration=5.0),
            TranscriptChunk(text="B", start=5.0, duration=5.0),
            TranscriptChunk(text="C", start=10.0, duration=3.0),
        ]
        transcript = VideoTranscript(video_id="abc123", chunks=chunks)
        
        result = chunker.chunk(transcript)
        
        # First chunk: 10 seconds, second chunk: 3 seconds remaining
        assert len(result) == 2
        assert result[0].duration == 10.0
        assert result[1].duration == 3.0
    
    def test_chunk_sentence(self):
        """Test sentence-based chunking."""
        config = ChunkingConfig(strategy=ChunkingStrategy.SENTENCE)
        chunker = TranscriptChunker(config)
        
        chunks = [
            TranscriptChunk(text="Hello world.", start=0.0, duration=5.0),
            TranscriptChunk(text="How are you?", start=5.0, duration=5.0),
            TranscriptChunk(text="I am fine.", start=10.0, duration=5.0),
        ]
        transcript = VideoTranscript(video_id="abc123", chunks=chunks)
        
        result = chunker.chunk(transcript)
        
        # Each sentence ends with punctuation
        assert len(result) == 3
        assert result[0].text == "Hello world."
        assert result[1].text == "How are you?"
        assert result[2].text == "I am fine."
    
    def test_chunk_sentence_combined(self):
        """Test sentence-based chunking with multiple chunks per sentence."""
        config = ChunkingConfig(strategy=ChunkingStrategy.SENTENCE)
        chunker = TranscriptChunker(config)
        
        chunks = [
            TranscriptChunk(text="Hello", start=0.0, duration=2.0),
            TranscriptChunk(text="world.", start=2.0, duration=3.0),
            TranscriptChunk(text="How", start=5.0, duration=2.0),
            TranscriptChunk(text="are you?", start=7.0, duration=3.0),
        ]
        transcript = VideoTranscript(video_id="abc123", chunks=chunks)
        
        result = chunker.chunk(transcript)
        
        # Two sentences
        assert len(result) == 2
        assert result[0].text == "Hello world."
        assert result[1].text == "How are you?"
    
    def test_chunk_semantic_fallback(self):
        """Test semantic chunking falls back to sentence."""
        config = ChunkingConfig(strategy=ChunkingStrategy.SEMANTIC)
        chunker = TranscriptChunker(config)
        
        chunks = [
            TranscriptChunk(text="Hello world.", start=0.0, duration=5.0),
            TranscriptChunk(text="How are you?", start=5.0, duration=5.0),
        ]
        transcript = VideoTranscript(video_id="abc123", chunks=chunks)
        
        result = chunker.chunk(transcript)
        
        # Falls back to sentence chunking
        assert len(result) == 2
    
    def test_chunk_default_strategy(self):
        """Test default strategy is fixed_size."""
        config = ChunkingConfig()  # Default is fixed_size
        chunker = TranscriptChunker(config)
        
        chunks = [
            TranscriptChunk(text="Hello", start=0.0, duration=5.0),
            TranscriptChunk(text="world", start=5.0, duration=5.0),
        ]
        transcript = VideoTranscript(video_id="abc123", chunks=chunks)
        
        result = chunker.chunk(transcript)
        
        # Should use fixed_size as default
        assert len(result) >= 1
    
    def test_chunk_with_overlap(self):
        """Test chunk_with_overlap method."""
        chunker = TranscriptChunker()
        
        chunks = [
            TranscriptChunk(text="A", start=0.0, duration=1.0),
            TranscriptChunk(text="B", start=1.0, duration=1.0),
            TranscriptChunk(text="C", start=2.0, duration=1.0),
            TranscriptChunk(text="D", start=3.0, duration=1.0),
        ]
        transcript = VideoTranscript(video_id="abc123", chunks=chunks)
        
        result = chunker.chunk_with_overlap(transcript, overlap_chunks=1)
        
        assert len(result) >= 1
