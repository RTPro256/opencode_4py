"""Tests for YouTube Timestamps module."""

import pytest
from unittest.mock import MagicMock, patch

from opencode.core.youtube.timestamps import (
    TimestampedResult,
    TimestampGenerator,
)


class TestTimestampedResult:
    """Tests for TimestampedResult."""
    
    def test_custom_values(self):
        """Test custom values."""
        result = TimestampedResult(
            text="Hello world",
            start_time=65.0,
            duration=10.0,
            video_id="abc123",
            youtube_url="https://www.youtube.com/watch?v=abc123&t=65s",
            end_time=75.0,
            relevance_score=0.95,
            metadata={"source": "test"}
        )
        assert result.text == "Hello world"
        assert result.start_time == 65.0
        assert result.duration == 10.0
        assert result.video_id == "abc123"
        assert result.end_time == 75.0
        assert result.relevance_score == 0.95
    
    def test_timestamp_str_under_minute(self):
        """Test timestamp_str for under a minute."""
        result = TimestampedResult(
            text="Test",
            start_time=45.0,
            duration=5.0,
            video_id="abc123",
            youtube_url="https://www.youtube.com/watch?v=abc123&t=45s",
            end_time=50.0
        )
        assert result.timestamp_str == "0:45"
    
    def test_timestamp_str_over_minute(self):
        """Test timestamp_str for over a minute."""
        result = TimestampedResult(
            text="Test",
            start_time=125.0,
            duration=5.0,
            video_id="abc123",
            youtube_url="https://www.youtube.com/watch?v=abc123&t=125s",
            end_time=130.0
        )
        assert result.timestamp_str == "2:05"
    
    def test_timestamp_str_over_hour(self):
        """Test timestamp_str for over an hour."""
        result = TimestampedResult(
            text="Test",
            start_time=3661.0,
            duration=5.0,
            video_id="abc123",
            youtube_url="https://www.youtube.com/watch?v=abc123&t=3661s",
            end_time=3666.0
        )
        assert result.timestamp_str == "1:01:01"
    
    def test_duration_str(self):
        """Test duration_str property."""
        result = TimestampedResult(
            text="Test",
            start_time=0.0,
            duration=125.0,
            video_id="abc123",
            youtube_url="https://www.youtube.com/watch?v=abc123&t=0s",
            end_time=125.0
        )
        assert result.duration_str == "2:05"
    
    def test_format_timestamp_seconds_only(self):
        """Test _format_timestamp with seconds only."""
        assert TimestampedResult._format_timestamp(30.0) == "0:30"
        assert TimestampedResult._format_timestamp(59.0) == "0:59"
    
    def test_format_timestamp_minutes(self):
        """Test _format_timestamp with minutes."""
        assert TimestampedResult._format_timestamp(90.0) == "1:30"
        assert TimestampedResult._format_timestamp(3599.0) == "59:59"
    
    def test_format_timestamp_hours(self):
        """Test _format_timestamp with hours."""
        assert TimestampedResult._format_timestamp(3600.0) == "1:00:00"
        assert TimestampedResult._format_timestamp(7325.0) == "2:02:05"
    
    def test_to_dict(self):
        """Test to_dict method."""
        result = TimestampedResult(
            text="Hello world",
            start_time=65.0,
            duration=10.0,
            video_id="abc123",
            youtube_url="https://www.youtube.com/watch?v=abc123&t=65s",
            end_time=75.0,
            relevance_score=0.95,
            metadata={"source": "test"}
        )
        d = result.to_dict()
        
        assert d["text"] == "Hello world"
        assert d["start_time"] == 65.0
        assert d["duration"] == 10.0
        assert d["video_id"] == "abc123"
        assert d["youtube_url"] == "https://www.youtube.com/watch?v=abc123&t=65s"
        assert d["end_time"] == 75.0
        assert d["timestamp"] == "1:05"
        assert d["relevance_score"] == 0.95
        assert d["metadata"]["source"] == "test"


class TestTimestampGenerator:
    """Tests for TimestampGenerator."""
    
    def test_init(self):
        """Test initialization."""
        generator = TimestampGenerator()
        assert generator.url_format == "watch"
        assert generator.include_end_time is False
    
    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        generator = TimestampGenerator(
            url_format="short",
            include_end_time=True
        )
        assert generator.url_format == "short"
        assert generator.include_end_time is True
    
    def test_create_timestamp_url_watch(self):
        """Test create_timestamp_url with watch format."""
        generator = TimestampGenerator(url_format="watch")
        url = generator.create_timestamp_url("abc123", 65.0)
        
        assert url == "https://www.youtube.com/watch?v=abc123&t=65s"
    
    def test_create_timestamp_url_short(self):
        """Test create_timestamp_url with short format."""
        generator = TimestampGenerator(url_format="short")
        url = generator.create_timestamp_url("abc123", 65.0)
        
        assert url == "https://youtu.be/abc123?t=65s"
    
    def test_create_timestamp_url_embed(self):
        """Test create_timestamp_url with embed format."""
        generator = TimestampGenerator(url_format="embed")
        url = generator.create_timestamp_url("abc123", 65.0)
        
        assert url == "https://www.youtube.com/embed/abc123?start=65"
    
    def test_create_result(self):
        """Test create_result method."""
        generator = TimestampGenerator()
        result = generator.create_result(
            text="Hello world",
            start_time=65.0,
            duration=10.0,
            video_id="abc123",
            relevance_score=0.95,
            metadata={"source": "test"}
        )
        
        assert result.text == "Hello world"
        assert result.start_time == 65.0
        assert result.duration == 10.0
        assert result.video_id == "abc123"
        assert result.youtube_url == "https://www.youtube.com/watch?v=abc123&t=65s"
        assert result.end_time == 75.0
        assert result.relevance_score == 0.95
    
    def test_create_result_without_score(self):
        """Test create_result without relevance score."""
        generator = TimestampGenerator()
        result = generator.create_result(
            text="Hello world",
            start_time=65.0,
            duration=10.0,
            video_id="abc123"
        )
        
        assert result.relevance_score is None
    
    def test_format_results(self):
        """Test format_results method."""
        generator = TimestampGenerator()
        results = [
            {"text": "Hello", "start": 0.0, "duration": 5.0, "score": 0.9},
            {"text": "World", "start": 10.0, "duration": 5.0, "relevance_score": 0.8},
        ]
        
        formatted = generator.format_results(results, "abc123")
        
        assert len(formatted) == 2
        assert formatted[0].text == "Hello"
        assert formatted[0].start_time == 0.0
        assert formatted[0].relevance_score == 0.9
        assert formatted[1].text == "World"
        assert formatted[1].start_time == 10.0
    
    def test_format_results_with_metadata(self):
        """Test format_results with metadata."""
        generator = TimestampGenerator()
        results = [
            {"text": "Hello", "start": 0.0, "duration": 5.0, "metadata": {"key": "value"}},
        ]
        
        formatted = generator.format_results(results, "abc123")
        
        assert formatted[0].metadata == {"key": "value"}
    
    def test_create_playlist_url(self):
        """Test create_playlist_url method."""
        generator = TimestampGenerator()
        url = generator.create_playlist_url("abc123", 10.0, 20.0)
        
        assert url == "https://www.youtube.com/watch?v=abc123&t=10s"
    
    def test_create_clip_url(self):
        """Test create_clip_url method."""
        generator = TimestampGenerator()
        url = generator.create_clip_url("abc123", 10.0, 20.0)
        
        assert url == "https://www.youtube.com/watch?v=abc123&t=10s"
    
    def test_parse_timestamp_seconds(self):
        """Test parse_timestamp with seconds only."""
        assert TimestampGenerator.parse_timestamp("30") == 30.0
        assert TimestampGenerator.parse_timestamp("45.5") == 45.5
    
    def test_parse_timestamp_minutes_seconds(self):
        """Test parse_timestamp with minutes and seconds."""
        assert TimestampGenerator.parse_timestamp("1:30") == 90.0
        assert TimestampGenerator.parse_timestamp("2:45") == 165.0
    
    def test_parse_timestamp_hours_minutes_seconds(self):
        """Test parse_timestamp with hours, minutes, and seconds."""
        assert TimestampGenerator.parse_timestamp("1:00:00") == 3600.0
        assert TimestampGenerator.parse_timestamp("1:30:45") == 5445.0
    
    def test_parse_timestamp_invalid(self):
        """Test parse_timestamp with invalid format."""
        with pytest.raises(ValueError):
            TimestampGenerator.parse_timestamp("1:2:3:4")
    
    def test_extract_timestamp_from_url(self):
        """Test extract_timestamp_from_url method."""
        url = "https://www.youtube.com/watch?v=abc123&t=65s"
        timestamp = TimestampGenerator.extract_timestamp_from_url(url)
        
        assert timestamp == 65
    
    def test_extract_timestamp_from_url_without_s(self):
        """Test extract_timestamp_from_url without 's' suffix."""
        url = "https://www.youtube.com/watch?v=abc123&t=65"
        timestamp = TimestampGenerator.extract_timestamp_from_url(url)
        
        assert timestamp == 65
    
    def test_extract_timestamp_from_url_no_timestamp(self):
        """Test extract_timestamp_from_url with no timestamp."""
        url = "https://www.youtube.com/watch?v=abc123"
        timestamp = TimestampGenerator.extract_timestamp_from_url(url)
        
        assert timestamp is None
    
    def test_extract_timestamp_from_short_url(self):
        """Test extract_timestamp_from_url with short URL."""
        url = "https://youtu.be/abc123?t=120s"
        timestamp = TimestampGenerator.extract_timestamp_from_url(url)
        
        assert timestamp == 120
