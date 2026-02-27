"""Tests for YouTube Transcript module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys

# Mock the optional dependencies before importing
mock_transcript_api = MagicMock()
sys.modules['youtube_transcript_api'] = mock_transcript_api
sys.modules['youtube_transcript_api._errors'] = MagicMock()

from opencode.core.youtube.transcript import (
    TranscriptChunk,
    VideoTranscript,
    YouTubeTranscriptExtractor,
    YOUTUBE_TRANSCRIPT_API_AVAILABLE,
)


class TestTranscriptChunk:
    """Tests for TranscriptChunk."""
    
    def test_default_values(self):
        """Test default values."""
        chunk = TranscriptChunk(
            text="Hello world",
            start=0.0,
            duration=5.0
        )
        assert chunk.text == "Hello world"
        assert chunk.start == 0.0
        assert chunk.duration == 5.0
    
    def test_end_property(self):
        """Test end property calculation."""
        chunk = TranscriptChunk(
            text="Hello world",
            start=10.0,
            duration=5.0
        )
        assert chunk.end == 15.0
    
    def test_to_dict(self):
        """Test to_dict method."""
        chunk = TranscriptChunk(
            text="Hello world",
            start=10.0,
            duration=5.0
        )
        d = chunk.to_dict()
        
        assert d["text"] == "Hello world"
        assert d["start"] == 10.0
        assert d["duration"] == 5.0


class TestVideoTranscript:
    """Tests for VideoTranscript."""
    
    def test_default_values(self):
        """Test default values."""
        transcript = VideoTranscript(video_id="abc123")
        assert transcript.video_id == "abc123"
        assert transcript.title is None
        assert transcript.author is None
        assert transcript.chunks == []
        assert transcript.language == "en"
    
    def test_custom_values(self):
        """Test custom values."""
        chunk = TranscriptChunk(text="Hello", start=0.0, duration=5.0)
        transcript = VideoTranscript(
            video_id="abc123",
            title="Test Video",
            author="Test Author",
            chunks=[chunk],
            language="es"
        )
        assert transcript.video_id == "abc123"
        assert transcript.title == "Test Video"
        assert transcript.author == "Test Author"
        assert len(transcript.chunks) == 1
        assert transcript.language == "es"
    
    def test_full_text(self):
        """Test full_text property."""
        chunk1 = TranscriptChunk(text="Hello", start=0.0, duration=5.0)
        chunk2 = TranscriptChunk(text="world", start=5.0, duration=5.0)
        transcript = VideoTranscript(
            video_id="abc123",
            chunks=[chunk1, chunk2]
        )
        
        assert transcript.full_text == "Hello world"
    
    def test_full_text_empty(self):
        """Test full_text with no chunks."""
        transcript = VideoTranscript(video_id="abc123")
        
        assert transcript.full_text == ""
    
    def test_total_duration(self):
        """Test total_duration property."""
        chunk1 = TranscriptChunk(text="Hello", start=0.0, duration=5.0)
        chunk2 = TranscriptChunk(text="world", start=5.0, duration=10.0)
        transcript = VideoTranscript(
            video_id="abc123",
            chunks=[chunk1, chunk2]
        )
        
        # Max end time is 15.0 (5.0 + 10.0)
        assert transcript.total_duration == 15.0
    
    def test_total_duration_empty(self):
        """Test total_duration with no chunks."""
        transcript = VideoTranscript(video_id="abc123")
        
        assert transcript.total_duration == 0.0
    
    def test_get_chunk_at_time(self):
        """Test get_chunk_at_time method."""
        chunk1 = TranscriptChunk(text="Hello", start=0.0, duration=5.0)
        chunk2 = TranscriptChunk(text="world", start=5.0, duration=5.0)
        transcript = VideoTranscript(
            video_id="abc123",
            chunks=[chunk1, chunk2]
        )
        
        # Find chunk at time 2.0
        result = transcript.get_chunk_at_time(2.0)
        assert result is not None
        assert result.text == "Hello"
        
        # Find chunk at time 7.0
        result = transcript.get_chunk_at_time(7.0)
        assert result is not None
        assert result.text == "world"
    
    def test_get_chunk_at_time_not_found(self):
        """Test get_chunk_at_time when time not in any chunk."""
        chunk1 = TranscriptChunk(text="Hello", start=0.0, duration=5.0)
        transcript = VideoTranscript(
            video_id="abc123",
            chunks=[chunk1]
        )
        
        # Time 10.0 is outside the chunk
        result = transcript.get_chunk_at_time(10.0)
        assert result is None


class TestYouTubeTranscriptExtractor:
    """Tests for YouTubeTranscriptExtractor."""
    
    def test_init_without_api(self):
        """Test initialization fails without youtube-transcript-api."""
        with patch('opencode.core.youtube.transcript.YOUTUBE_TRANSCRIPT_API_AVAILABLE', False):
            with pytest.raises(ImportError) as exc_info:
                YouTubeTranscriptExtractor()
            assert "youtube-transcript-api" in str(exc_info.value).lower()
    
    def test_init_with_api(self):
        """Test initialization with API available."""
        with patch('opencode.core.youtube.transcript.YOUTUBE_TRANSCRIPT_API_AVAILABLE', True):
            extractor = YouTubeTranscriptExtractor()
            assert extractor.preferred_languages == ["en"]
            assert extractor.preserve_formatting is False
            assert extractor.proxy is None
    
    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        with patch('opencode.core.youtube.transcript.YOUTUBE_TRANSCRIPT_API_AVAILABLE', True):
            extractor = YouTubeTranscriptExtractor(
                preferred_languages=["es", "en"],
                preserve_formatting=True,
                proxy={"http": "http://proxy:8080"}
            )
            assert extractor.preferred_languages == ["es", "en"]
            assert extractor.preserve_formatting is True
            assert extractor.proxy == {"http": "http://proxy:8080"}
    
    def test_extract_video_id_standard_url(self):
        """Test extract_video_id from standard URL."""
        with patch('opencode.core.youtube.transcript.YOUTUBE_TRANSCRIPT_API_AVAILABLE', True):
            extractor = YouTubeTranscriptExtractor()
            
            video_id = extractor.extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
            assert video_id == "dQw4w9WgXcQ"
    
    def test_extract_video_id_short_url(self):
        """Test extract_video_id from short URL."""
        with patch('opencode.core.youtube.transcript.YOUTUBE_TRANSCRIPT_API_AVAILABLE', True):
            extractor = YouTubeTranscriptExtractor()
            
            video_id = extractor.extract_video_id("https://youtu.be/dQw4w9WgXcQ")
            assert video_id == "dQw4w9WgXcQ"
    
    def test_extract_video_id_embed_url(self):
        """Test extract_video_id from embed URL."""
        with patch('opencode.core.youtube.transcript.YOUTUBE_TRANSCRIPT_API_AVAILABLE', True):
            extractor = YouTubeTranscriptExtractor()
            
            video_id = extractor.extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ")
            assert video_id == "dQw4w9WgXcQ"
    
    def test_extract_video_id_shorts_url(self):
        """Test extract_video_id from shorts URL."""
        with patch('opencode.core.youtube.transcript.YOUTUBE_TRANSCRIPT_API_AVAILABLE', True):
            extractor = YouTubeTranscriptExtractor()
            
            video_id = extractor.extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ")
            assert video_id == "dQw4w9WgXcQ"
    
    def test_extract_video_id_direct(self):
        """Test extract_video_id from direct video ID."""
        with patch('opencode.core.youtube.transcript.YOUTUBE_TRANSCRIPT_API_AVAILABLE', True):
            extractor = YouTubeTranscriptExtractor()
            
            video_id = extractor.extract_video_id("dQw4w9WgXcQ")
            assert video_id == "dQw4w9WgXcQ"
    
    def test_extract_video_id_invalid(self):
        """Test extract_video_id with invalid URL."""
        with patch('opencode.core.youtube.transcript.YOUTUBE_TRANSCRIPT_API_AVAILABLE', True):
            extractor = YouTubeTranscriptExtractor()
            
            with pytest.raises(ValueError) as exc_info:
                extractor.extract_video_id("https://example.com/video")
            assert "Invalid YouTube URL" in str(exc_info.value)
    
    def test_fetch_transcript(self):
        """Test fetch_transcript method."""
        mock_api = MagicMock()
        mock_api.get_transcript.return_value = [
            {"text": "Hello world", "start": 0.0, "duration": 5.0},
            {"text": "This is a test", "start": 5.0, "duration": 5.0},
        ]
        
        with patch('opencode.core.youtube.transcript.YOUTUBE_TRANSCRIPT_API_AVAILABLE', True):
            with patch('opencode.core.youtube.transcript.YouTubeTranscriptApi', mock_api):
                extractor = YouTubeTranscriptExtractor()
                result = extractor.fetch_transcript("dQw4w9WgXcQ")
                
                assert result.video_id == "dQw4w9WgXcQ"
                assert len(result.chunks) == 2
                assert result.chunks[0].text == "Hello world"
    
    def test_fetch_transcript_with_url(self):
        """Test fetch_transcript with full URL."""
        mock_api = MagicMock()
        mock_api.get_transcript.return_value = [
            {"text": "Hello", "start": 0.0, "duration": 5.0},
        ]
        
        with patch('opencode.core.youtube.transcript.YOUTUBE_TRANSCRIPT_API_AVAILABLE', True):
            with patch('opencode.core.youtube.transcript.YouTubeTranscriptApi', mock_api):
                extractor = YouTubeTranscriptExtractor()
                result = extractor.fetch_transcript("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
                
                assert result.video_id == "dQw4w9WgXcQ"
    
    def test_fetch_transcript_with_fallback(self):
        """Test fetch_transcript_with_fallback method - basic success case."""
        mock_api = MagicMock()
        mock_api.get_transcript.return_value = [
            {"text": "Hello world", "start": 0.0, "duration": 5.0},
        ]
        
        with patch('opencode.core.youtube.transcript.YOUTUBE_TRANSCRIPT_API_AVAILABLE', True):
            with patch('opencode.core.youtube.transcript.YouTubeTranscriptApi', mock_api):
                extractor = YouTubeTranscriptExtractor(preferred_languages=["en"])
                result = extractor.fetch_transcript_with_fallback(
                    "dQw4w9WgXcQ",
                    fallback_languages=["es"]
                )
                
                assert result.video_id == "dQw4w9WgXcQ"
                assert len(result.chunks) == 1
                assert result.chunks[0].text == "Hello world"
    
    def test_list_available_transcripts(self):
        """Test list_available_transcripts method."""
        mock_transcript = MagicMock()
        mock_transcript.language = "English"
        mock_transcript.language_code = "en"
        mock_transcript.is_generated = False
        mock_transcript.is_translatable = True
        
        mock_api = MagicMock()
        mock_api.list_transcripts.return_value = [mock_transcript]
        
        with patch('opencode.core.youtube.transcript.YOUTUBE_TRANSCRIPT_API_AVAILABLE', True):
            with patch('opencode.core.youtube.transcript.YouTubeTranscriptApi', mock_api):
                extractor = YouTubeTranscriptExtractor()
                result = extractor.list_available_transcripts("dQw4w9WgXcQ")
                
                assert len(result) == 1
                assert result[0]["language"] == "English"
                assert result[0]["language_code"] == "en"
    
    def test_list_available_transcripts_error(self):
        """Test list_available_transcripts handles errors."""
        mock_api = MagicMock()
        mock_api.list_transcripts.side_effect = Exception("API Error")
        
        with patch('opencode.core.youtube.transcript.YOUTUBE_TRANSCRIPT_API_AVAILABLE', True):
            with patch('opencode.core.youtube.transcript.YouTubeTranscriptApi', mock_api):
                extractor = YouTubeTranscriptExtractor()
                result = extractor.list_available_transcripts("dQw4w9WgXcQ")
                
                assert result == []
    
    @pytest.mark.asyncio
    async def test_fetch_transcript_async(self):
        """Test async transcript fetching."""
        with patch('opencode.core.youtube.transcript.YOUTUBE_TRANSCRIPT_API_AVAILABLE', True):
            extractor = YouTubeTranscriptExtractor()
            
            mock_transcript = VideoTranscript(
                video_id="dQw4w9WgXcQ",
                chunks=[TranscriptChunk(text="Hello", start=0.0, duration=5.0)]
            )
            
            with patch('asyncio.get_event_loop') as mock_loop:
                mock_loop.return_value.run_in_executor = AsyncMock(
                    return_value=mock_transcript
                )
                result = await extractor.fetch_transcript_async("dQw4w9WgXcQ")
                
                assert result.video_id == "dQw4w9WgXcQ"
                assert result.chunks[0].text == "Hello"