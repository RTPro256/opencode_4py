"""
YouTube RAG Integration Module

This module provides comprehensive YouTube video processing and RAG capabilities:
- Transcript extraction and chunking
- Channel-level indexing
- Timestamped search results
- Multimodal processing (frames + audio)
"""

from .transcript import YouTubeTranscriptExtractor, TranscriptChunk
from .channel import YouTubeChannelIndexer, ChannelStats
from .timestamps import TimestampGenerator, TimestampedResult
from .chunking import TranscriptChunker, ChunkingConfig

__all__ = [
    "YouTubeTranscriptExtractor",
    "TranscriptChunk",
    "YouTubeChannelIndexer",
    "ChannelStats",
    "TimestampGenerator",
    "TimestampedResult",
    "TranscriptChunker",
    "ChunkingConfig",
]
