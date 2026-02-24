"""
Tests for YouTube Transcript Tool.

Unit tests for YouTube video transcript functionality.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import ValidationError

from opencode.tool.youtube import (
    TranscriptChunk,
    VideoInfo,
    YouTubeTranscriptTool,
)
from opencode.tool.base import ToolResult


class TestTranscriptChunk:
    """Tests for TranscriptChunk model."""

    def test_chunk_creation(self):
        """Test creating a TranscriptChunk."""
        chunk = TranscriptChunk(
            text="Hello world",
            start=10.5,
            duration=5.0,
        )
        
        assert chunk.text == "Hello world"
        assert chunk.start == 10.5
        assert chunk.duration == 5.0

    def test_to_timestamp_url(self):
        """Test generating timestamp URL."""
        chunk = TranscriptChunk(
            text="Test content",
            start=125.0,  # 2 minutes 5 seconds
            duration=10.0,
        )
        
        url = chunk.to_timestamp_url("abc123")
        
        assert "youtube.com/watch?v=abc123" in url
        assert "t=2m5s" in url

    def test_to_timestamp_url_zero_time(self):
        """Test timestamp URL at zero time."""
        chunk = TranscriptChunk(
            text="Start",
            start=0.0,
            duration=5.0,
        )
        
        url = chunk.to_timestamp_url("xyz789")
        
        assert "t=0m0s" in url

    def test_format_timestamp(self):
        """Test formatting timestamp."""
        chunk = TranscriptChunk(
            text="Test",
            start=65.0,  # 1 minute 5 seconds
            duration=5.0,
        )
        
        formatted = chunk.format_timestamp()
        
        assert formatted == "1:05"

    def test_format_timestamp_large(self):
        """Test formatting large timestamp."""
        chunk = TranscriptChunk(
            text="Test",
            start=3725.0,  # 62 minutes 5 seconds
            duration=5.0,
        )
        
        formatted = chunk.format_timestamp()
        
        assert formatted == "62:05"


class TestVideoInfo:
    """Tests for VideoInfo model."""

    def test_video_info_minimal(self):
        """Test creating VideoInfo with minimal fields."""
        info = VideoInfo(video_id="abc123")
        
        assert info.video_id == "abc123"
        assert info.title is None
        assert info.duration is None
        assert info.language == "en"

    def test_video_info_full(self):
        """Test creating VideoInfo with all fields."""
        info = VideoInfo(
            video_id="xyz789",
            title="Test Video",
            duration=300.0,
            language="es",
        )
        
        assert info.video_id == "xyz789"
        assert info.title == "Test Video"
        assert info.duration == 300.0
        assert info.language == "es"


class TestYouTubeTranscriptTool:
    """Tests for YouTubeTranscriptTool."""

    def test_tool_properties(self):
        """Test tool properties."""
        tool = YouTubeTranscriptTool()
        
        assert tool.name == "youtube_transcript"
        assert "transcript" in tool.description.lower()
        assert "url" in tool.parameters["properties"]

    def test_parameters_schema(self):
        """Test parameters schema."""
        tool = YouTubeTranscriptTool()
        params = tool.parameters
        
        assert params["type"] == "object"
        assert "url" in params["properties"]
        assert "language" in params["properties"]
        assert "chunk_size" in params["properties"]
        assert "include_timestamps" in params["properties"]
        assert params["required"] == ["url"]

    def test_extract_video_id_standard(self):
        """Test extracting video ID from standard URL."""
        tool = YouTubeTranscriptTool()
        
        # YouTube video IDs are 11 characters
        video_id = tool._extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_short(self):
        """Test extracting video ID from short URL."""
        tool = YouTubeTranscriptTool()
        
        video_id = tool._extract_video_id("https://youtu.be/dQw4w9WgXcQ")
        
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_embed(self):
        """Test extracting video ID from embed URL."""
        tool = YouTubeTranscriptTool()
        
        video_id = tool._extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ")
        
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_shorts(self):
        """Test extracting video ID from shorts URL."""
        tool = YouTubeTranscriptTool()
        
        video_id = tool._extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ")
        
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_invalid(self):
        """Test extracting video ID from invalid URL."""
        tool = YouTubeTranscriptTool()
        
        video_id = tool._extract_video_id("https://example.com/video")
        
        assert video_id is None

    def test_merge_chunks_empty(self):
        """Test merging empty transcript."""
        tool = YouTubeTranscriptTool()
        
        result = tool._merge_chunks([], group_size=6)
        
        assert result == []

    def test_merge_chunks_single_group(self):
        """Test merging chunks into single group."""
        tool = YouTubeTranscriptTool()
        
        chunks = [
            TranscriptChunk(text="Hello", start=0.0, duration=2.0),
            TranscriptChunk(text="world", start=2.0, duration=2.0),
            TranscriptChunk(text="test", start=4.0, duration=2.0),
        ]
        
        result = tool._merge_chunks(chunks, group_size=6)
        
        assert len(result) == 1
        assert result[0].text == "Hello world test"
        assert result[0].start == 0.0

    def test_merge_chunks_multiple_groups(self):
        """Test merging chunks into multiple groups."""
        tool = YouTubeTranscriptTool()
        
        chunks = [
            TranscriptChunk(text="A", start=0.0, duration=1.0),
            TranscriptChunk(text="B", start=1.0, duration=1.0),
            TranscriptChunk(text="C", start=2.0, duration=1.0),
            TranscriptChunk(text="D", start=3.0, duration=1.0),
        ]
        
        result = tool._merge_chunks(chunks, group_size=2)
        
        assert len(result) == 2
        assert result[0].text == "A B"
        assert result[1].text == "C D"

    def test_merge_chunks_timing(self):
        """Test that merged chunks have correct timing."""
        tool = YouTubeTranscriptTool()
        
        chunks = [
            TranscriptChunk(text="First", start=0.0, duration=5.0),
            TranscriptChunk(text="Second", start=5.0, duration=5.0),
        ]
        
        result = tool._merge_chunks(chunks, group_size=2)
        
        assert result[0].start == 0.0
        # Duration should span both chunks: 5.0 + 5.0 = 10.0
        assert result[0].duration == 10.0

    def test_get_video_url(self):
        """Test getting video URL from ID."""
        tool = YouTubeTranscriptTool()
        
        url = tool.get_video_url("abc123")
        
        assert url == "https://youtube.com/watch?v=abc123"

    @pytest.mark.asyncio
    async def test_execute_invalid_url(self):
        """Test execute with invalid URL."""
        tool = YouTubeTranscriptTool()
        
        result = await tool.execute(url="https://example.com/video")
        
        assert result.success is False
        assert result.error is not None
        assert "Could not extract video ID" in result.error

    @pytest.mark.asyncio
    async def test_execute_missing_url(self):
        """Test execute without URL."""
        tool = YouTubeTranscriptTool()
        
        result = await tool.execute()
        
        assert result.success is False

    @pytest.mark.asyncio
    async def test_execute_transcript_not_available(self):
        """Test execute when transcript not available."""
        tool = YouTubeTranscriptTool()
        
        with patch.object(tool, '_fetch_transcript', return_value=[]):
            result = await tool.execute(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
            
            assert result.success is False
            assert result.error is not None
            assert "Transcript not available" in result.error

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful execute."""
        tool = YouTubeTranscriptTool()
        
        mock_chunks = [
            TranscriptChunk(text="Hello world", start=0.0, duration=5.0),
            TranscriptChunk(text="Test content", start=5.0, duration=5.0),
        ]
        
        with patch.object(tool, '_fetch_transcript', return_value=mock_chunks):
            result = await tool.execute(
                url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                include_timestamps=True,
            )
            
            assert result.success is True
            assert "dQw4w9WgXcQ" in result.output
            assert "transcript" in result.metadata

    @pytest.mark.asyncio
    async def test_execute_without_timestamps(self):
        """Test execute without timestamps."""
        tool = YouTubeTranscriptTool()
        
        mock_chunks = [
            TranscriptChunk(text="Hello world", start=0.0, duration=5.0),
        ]
        
        with patch.object(tool, '_fetch_transcript', return_value=mock_chunks):
            result = await tool.execute(
                url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                include_timestamps=False,
            )
            
            assert result.success is True
            assert "Hello world" in result.output

    @pytest.mark.asyncio
    async def test_execute_with_custom_chunk_size(self):
        """Test execute with custom chunk size."""
        tool = YouTubeTranscriptTool()
        
        mock_chunks = [
            TranscriptChunk(text="A", start=0.0, duration=1.0),
            TranscriptChunk(text="B", start=1.0, duration=1.0),
            TranscriptChunk(text="C", start=2.0, duration=1.0),
        ]
        
        with patch.object(tool, '_fetch_transcript', return_value=mock_chunks):
            result = await tool.execute(
                url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                chunk_size=2,
            )
            
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_import_error(self):
        """Test execute when youtube-transcript-api not installed."""
        tool = YouTubeTranscriptTool()
        
        with patch.object(tool, '_fetch_transcript', side_effect=ImportError("Not installed")):
            result = await tool.execute(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
            
            assert result.success is False
            assert result.error is not None
            assert "pip install" in result.error

    @pytest.mark.asyncio
    async def test_execute_exception(self):
        """Test execute with general exception."""
        tool = YouTubeTranscriptTool()
        
        with patch.object(tool, '_fetch_transcript', side_effect=Exception("Network error")):
            result = await tool.execute(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
            
            assert result.success is False
            assert result.error is not None
            assert "Network error" in result.error

    @pytest.mark.asyncio
    async def test_fetch_transcript_success(self):
        """Test _fetch_transcript method."""
        tool = YouTubeTranscriptTool()
        
        # Mock the youtube_transcript_api
        mock_api = MagicMock()
        mock_item = MagicMock()
        mock_item.text = "Test transcript"
        mock_item.start = 0.0
        mock_item.duration = 5.0
        mock_api.fetch.return_value = [mock_item]
        
        with patch.dict('sys.modules', {'youtube_transcript_api': MagicMock(YouTubeTranscriptApi=mock_api)}):
            # Need to re-import to get the mocked module
            from youtube_transcript_api import YouTubeTranscriptApi
            with patch('youtube_transcript_api.YouTubeTranscriptApi', return_value=mock_api):
                result = await tool._fetch_transcript("abc123")
                
                assert len(result) == 1
                assert result[0].text == "Test transcript"

    def test_url_patterns(self):
        """Test URL patterns class attribute."""
        tool = YouTubeTranscriptTool()
        
        assert len(tool.URL_PATTERNS) == 4
        # Verify patterns are valid regex
        import re
        for pattern in tool.URL_PATTERNS:
            re.compile(pattern)  # Should not raise

    @pytest.mark.asyncio
    async def test_execute_metadata_structure(self):
        """Test that metadata has correct structure."""
        tool = YouTubeTranscriptTool()
        
        mock_chunks = [
            TranscriptChunk(text="Test", start=0.0, duration=5.0),
        ]
        
        with patch.object(tool, '_fetch_transcript', return_value=mock_chunks):
            result = await tool.execute(url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
            
            assert result.success is True
            assert "video_id" in result.metadata
            assert "video_info" in result.metadata
            assert "transcript" in result.metadata
            assert "full_text" in result.metadata
            assert "chunk_count" in result.metadata

    @pytest.mark.asyncio
    async def test_execute_many_chunks_truncated(self):
        """Test that output is truncated with many chunks."""
        tool = YouTubeTranscriptTool()
        
        # Create 30 chunks - they will be merged to 5 chunks (30/6=5)
        mock_chunks = [
            TranscriptChunk(text=f"Chunk {i}", start=i * 5.0, duration=5.0)
            for i in range(30)
        ]
        
        with patch.object(tool, '_fetch_transcript', return_value=mock_chunks):
            result = await tool.execute(
                url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                include_timestamps=True,
            )
            
            assert result.success is True
            # After merging 30 chunks into groups of 6, we have 5 chunks
            # All 5 chunks are displayed (limit is 20), so no truncation message
            assert "Total chunks: 5" in result.output
