"""
Tests for YouTube Channel Indexer.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime

from opencode.core.youtube.channel import (
    ChannelStats,
    VideoInfo,
)


@pytest.mark.unit
class TestChannelStats:
    """Tests for ChannelStats model."""

    def test_channel_stats_creation(self):
        """Test creating ChannelStats."""
        stats = ChannelStats(
            channel_id="UC123456",
            channel_title="Test Channel",
            total_videos=100,
            indexed_videos=50,
            total_chunks=500,
            total_duration_seconds=36000.0,
            languages=["en", "es"],
        )
        assert stats.channel_id == "UC123456"
        assert stats.channel_title == "Test Channel"
        assert stats.total_videos == 100
        assert stats.indexed_videos == 50
        assert stats.total_chunks == 500
        assert stats.total_duration_seconds == 36000.0
        assert stats.languages == ["en", "es"]

    def test_channel_stats_total_duration_hours(self):
        """Test total_duration_hours property."""
        stats = ChannelStats(
            channel_id="UC123",
            channel_title="Test",
            total_duration_seconds=7200.0,  # 2 hours
        )
        assert stats.total_duration_hours == 2.0

    def test_channel_stats_to_dict(self):
        """Test to_dict method."""
        now = datetime.now()
        stats = ChannelStats(
            channel_id="UC123",
            channel_title="Test Channel",
            total_videos=10,
            indexed_videos=5,
            total_chunks=50,
            total_duration_seconds=3600.0,
            last_indexed=now,
            languages=["en"],
        )
        result = stats.to_dict()
        assert result["channel_id"] == "UC123"
        assert result["channel_title"] == "Test Channel"
        assert result["total_videos"] == 10
        assert result["indexed_videos"] == 5
        assert result["total_chunks"] == 50
        assert result["total_duration_seconds"] == 3600.0
        assert result["total_duration_hours"] == 1.0
        assert result["last_indexed"] == now.isoformat()
        assert result["languages"] == ["en"]

    def test_channel_stats_to_dict_no_last_indexed(self):
        """Test to_dict with no last_indexed."""
        stats = ChannelStats(
            channel_id="UC123",
            channel_title="Test",
        )
        result = stats.to_dict()
        assert result["last_indexed"] is None


@pytest.mark.unit
class TestVideoInfo:
    """Tests for VideoInfo model."""

    def test_video_info_creation(self):
        """Test creating VideoInfo."""
        now = datetime.now()
        info = VideoInfo(
            video_id="abc123",
            title="Test Video",
            description="A test video",
            published_at=now,
            duration="PT10M30S",
            view_count=1000,
            like_count=100,
            comment_count=50,
            thumbnail_url="https://example.com/thumb.jpg",
        )
        assert info.video_id == "abc123"
        assert info.title == "Test Video"
        assert info.description == "A test video"
        assert info.published_at == now
        assert info.duration == "PT10M30S"
        assert info.view_count == 1000
        assert info.like_count == 100
        assert info.comment_count == 50
        assert info.thumbnail_url == "https://example.com/thumb.jpg"

    def test_video_info_defaults(self):
        """Test VideoInfo default values."""
        info = VideoInfo(video_id="abc123", title="Test")
        assert info.description == ""
        assert info.published_at is None
        assert info.duration == ""
        assert info.view_count == 0
        assert info.like_count == 0
        assert info.comment_count == 0
        assert info.thumbnail_url == ""

    def test_video_info_to_dict(self):
        """Test to_dict method."""
        now = datetime.now()
        info = VideoInfo(
            video_id="abc123",
            title="Test Video",
            description="A test video",
            published_at=now,
            duration="PT10M",
            view_count=1000,
            like_count=100,
            comment_count=50,
            thumbnail_url="https://example.com/thumb.jpg",
        )
        result = info.to_dict()
        assert result["video_id"] == "abc123"
        assert result["title"] == "Test Video"
        assert result["description"] == "A test video"
        assert result["published_at"] == now.isoformat()
        assert result["duration"] == "PT10M"
        assert result["view_count"] == 1000
        assert result["like_count"] == 100
        assert result["comment_count"] == 50
        assert result["thumbnail_url"] == "https://example.com/thumb.jpg"

    def test_video_info_to_dict_no_published_at(self):
        """Test to_dict with no published_at."""
        info = VideoInfo(video_id="abc", title="Test")
        result = info.to_dict()
        assert result["published_at"] is None


@pytest.mark.unit
class TestYouTubeChannelIndexer:
    """Tests for YouTubeChannelIndexer."""

    @patch("opencode.core.youtube.channel.GOOGLE_API_AVAILABLE", True)
    @patch("opencode.core.youtube.channel.build")
    def test_init_with_api_key(self, mock_build):
        """Test initialization with API key."""
        from opencode.core.youtube.channel import YouTubeChannelIndexer
        mock_extractor = MagicMock()
        mock_chunker = MagicMock()
        indexer = YouTubeChannelIndexer(
            api_key="test_key",
            transcript_extractor=mock_extractor,
            chunker=mock_chunker,
        )
        assert indexer.api_key == "test_key"
        assert indexer.youtube is None
        assert indexer.transcript_extractor == mock_extractor
        assert indexer.chunker == mock_chunker

    @patch("opencode.core.youtube.channel.GOOGLE_API_AVAILABLE", True)
    @patch("opencode.core.youtube.channel.build")
    def test_get_youtube_client(self, mock_build):
        """Test _get_youtube_client creates client."""
        from opencode.core.youtube.channel import YouTubeChannelIndexer
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_extractor = MagicMock()
        mock_chunker = MagicMock()

        indexer = YouTubeChannelIndexer(
            api_key="test_key",
            transcript_extractor=mock_extractor,
            chunker=mock_chunker,
        )
        client = indexer._get_youtube_client()

        assert client == mock_youtube
        mock_build.assert_called_once_with("youtube", "v3", developerKey="test_key")

    @patch("opencode.core.youtube.channel.GOOGLE_API_AVAILABLE", True)
    @patch("opencode.core.youtube.channel.build")
    def test_get_youtube_client_cached(self, mock_build):
        """Test _get_youtube_client caches client."""
        from opencode.core.youtube.channel import YouTubeChannelIndexer
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_extractor = MagicMock()
        mock_chunker = MagicMock()

        indexer = YouTubeChannelIndexer(
            api_key="test_key",
            transcript_extractor=mock_extractor,
            chunker=mock_chunker,
        )
        client1 = indexer._get_youtube_client()
        client2 = indexer._get_youtube_client()

        assert client1 == client2
        mock_build.assert_called_once()

    @patch("opencode.core.youtube.channel.GOOGLE_API_AVAILABLE", True)
    @patch("opencode.core.youtube.channel.build")
    def test_get_youtube_client_no_key(self, mock_build):
        """Test _get_youtube_client raises without key."""
        from opencode.core.youtube.channel import YouTubeChannelIndexer
        mock_extractor = MagicMock()
        mock_chunker = MagicMock()
        indexer = YouTubeChannelIndexer(
            api_key=None,
            transcript_extractor=mock_extractor,
            chunker=mock_chunker,
        )
        with pytest.raises(ValueError, match="YouTube API key is required"):
            indexer._get_youtube_client()

    @patch("opencode.core.youtube.channel.GOOGLE_API_AVAILABLE", True)
    @patch("opencode.core.youtube.channel.build")
    def test_get_channel_id(self, mock_build):
        """Test get_channel_id."""
        from opencode.core.youtube.channel import YouTubeChannelIndexer
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_youtube.search().list().execute.return_value = {
            "items": [{"snippet": {"channelId": "UC123456"}}]
        }
        mock_extractor = MagicMock()
        mock_chunker = MagicMock()

        indexer = YouTubeChannelIndexer(
            api_key="test_key",
            transcript_extractor=mock_extractor,
            chunker=mock_chunker,
        )
        result = indexer.get_channel_id("@testchannel")

        assert result == "UC123456"
        mock_youtube.search().list.assert_called()

    @patch("opencode.core.youtube.channel.GOOGLE_API_AVAILABLE", True)
    @patch("opencode.core.youtube.channel.build")
    def test_get_channel_id_without_at(self, mock_build):
        """Test get_channel_id without @ prefix."""
        from opencode.core.youtube.channel import YouTubeChannelIndexer
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_youtube.search().list().execute.return_value = {
            "items": [{"snippet": {"channelId": "UC123456"}}]
        }
        mock_extractor = MagicMock()
        mock_chunker = MagicMock()

        indexer = YouTubeChannelIndexer(
            api_key="test_key",
            transcript_extractor=mock_extractor,
            chunker=mock_chunker,
        )
        result = indexer.get_channel_id("testchannel")

        assert result == "UC123456"

    @patch("opencode.core.youtube.channel.GOOGLE_API_AVAILABLE", True)
    @patch("opencode.core.youtube.channel.build")
    def test_get_channel_id_not_found(self, mock_build):
        """Test get_channel_id raises when not found."""
        from opencode.core.youtube.channel import YouTubeChannelIndexer
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_youtube.search().list().execute.return_value = {"items": []}
        mock_extractor = MagicMock()
        mock_chunker = MagicMock()

        indexer = YouTubeChannelIndexer(
            api_key="test_key",
            transcript_extractor=mock_extractor,
            chunker=mock_chunker,
        )
        with pytest.raises(ValueError, match="Channel not found"):
            indexer.get_channel_id("@nonexistent")

    @patch("opencode.core.youtube.channel.GOOGLE_API_AVAILABLE", True)
    @patch("opencode.core.youtube.channel.build")
    def test_get_channel_info(self, mock_build):
        """Test get_channel_info."""
        from opencode.core.youtube.channel import YouTubeChannelIndexer
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_youtube.channels().list().execute.return_value = {
            "items": [{
                "snippet": {"title": "Test Channel", "description": "A test channel"},
                "statistics": {
                    "subscriberCount": "1000",
                    "videoCount": "50",
                    "viewCount": "10000",
                },
                "contentDetails": {
                    "relatedPlaylists": {"uploads": "UU123456"}
                },
            }]
        }
        mock_extractor = MagicMock()
        mock_chunker = MagicMock()

        indexer = YouTubeChannelIndexer(
            api_key="test_key",
            transcript_extractor=mock_extractor,
            chunker=mock_chunker,
        )
        result = indexer.get_channel_info("UC123456")

        assert result["channel_id"] == "UC123456"
        assert result["title"] == "Test Channel"
        assert result["description"] == "A test channel"
        assert result["subscriber_count"] == 1000
        assert result["video_count"] == 50
        assert result["view_count"] == 10000
        assert result["uploads_playlist_id"] == "UU123456"

    @patch("opencode.core.youtube.channel.GOOGLE_API_AVAILABLE", True)
    @patch("opencode.core.youtube.channel.build")
    def test_get_channel_info_not_found(self, mock_build):
        """Test get_channel_info raises when not found."""
        from opencode.core.youtube.channel import YouTubeChannelIndexer
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_youtube.channels().list().execute.return_value = {"items": []}
        mock_extractor = MagicMock()
        mock_chunker = MagicMock()

        indexer = YouTubeChannelIndexer(
            api_key="test_key",
            transcript_extractor=mock_extractor,
            chunker=mock_chunker,
        )
        with pytest.raises(ValueError, match="Channel not found"):
            indexer.get_channel_info("UC_nonexistent")

    @patch("opencode.core.youtube.channel.GOOGLE_API_AVAILABLE", True)
    @patch("opencode.core.youtube.channel.build")
    def test_get_video_ids(self, mock_build):
        """Test get_video_ids."""
        from opencode.core.youtube.channel import YouTubeChannelIndexer
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube

        # Mock channel info
        mock_youtube.channels().list().execute.return_value = {
            "items": [{
                "snippet": {"title": "Test", "description": ""},
                "statistics": {"subscriberCount": "0", "videoCount": "2", "viewCount": "0"},
                "contentDetails": {"relatedPlaylists": {"uploads": "UU123"}},
            }]
        }

        # Mock playlist items
        mock_youtube.playlistItems().list().execute.return_value = {
            "items": [
                {"contentDetails": {"videoId": "video1"}},
                {"contentDetails": {"videoId": "video2"}},
            ],
            "nextPageToken": None,
        }
        mock_extractor = MagicMock()
        mock_chunker = MagicMock()

        indexer = YouTubeChannelIndexer(
            api_key="test_key",
            transcript_extractor=mock_extractor,
            chunker=mock_chunker,
        )
        result = indexer.get_video_ids("UC123")

        assert result == ["video1", "video2"]

    @patch("opencode.core.youtube.channel.GOOGLE_API_AVAILABLE", True)
    @patch("opencode.core.youtube.channel.build")
    def test_get_video_ids_with_max(self, mock_build):
        """Test get_video_ids with max_videos."""
        from opencode.core.youtube.channel import YouTubeChannelIndexer
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube

        # Mock channel info
        mock_youtube.channels().list().execute.return_value = {
            "items": [{
                "snippet": {"title": "Test", "description": ""},
                "statistics": {"subscriberCount": "0", "videoCount": "5", "viewCount": "0"},
                "contentDetails": {"relatedPlaylists": {"uploads": "UU123"}},
            }]
        }

        # Mock playlist items
        mock_youtube.playlistItems().list().execute.return_value = {
            "items": [
                {"contentDetails": {"videoId": "video1"}},
                {"contentDetails": {"videoId": "video2"}},
                {"contentDetails": {"videoId": "video3"}},
            ],
            "nextPageToken": None,
        }
        mock_extractor = MagicMock()
        mock_chunker = MagicMock()

        indexer = YouTubeChannelIndexer(
            api_key="test_key",
            transcript_extractor=mock_extractor,
            chunker=mock_chunker,
        )
        result = indexer.get_video_ids("UC123", max_videos=2)

        assert result == ["video1", "video2"]

    @patch("opencode.core.youtube.channel.GOOGLE_API_AVAILABLE", True)
    @patch("opencode.core.youtube.channel.build")
    def test_get_video_info(self, mock_build):
        """Test get_video_info."""
        from opencode.core.youtube.channel import YouTubeChannelIndexer
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_youtube.videos().list().execute.return_value = {
            "items": [{
                "snippet": {
                    "title": "Test Video",
                    "description": "A test video",
                    "publishedAt": "2024-01-01T00:00:00Z",
                    "thumbnails": {"high": {"url": "https://example.com/thumb.jpg"}},
                },
                "statistics": {
                    "viewCount": "1000",
                    "likeCount": "100",
                    "commentCount": "50",
                },
                "contentDetails": {"duration": "PT10M"},
            }]
        }
        mock_extractor = MagicMock()
        mock_chunker = MagicMock()

        indexer = YouTubeChannelIndexer(
            api_key="test_key",
            transcript_extractor=mock_extractor,
            chunker=mock_chunker,
        )
        result = indexer.get_video_info("abc123")

        assert result.video_id == "abc123"
        assert result.title == "Test Video"
        assert result.description == "A test video"
        assert result.duration == "PT10M"
        assert result.view_count == 1000
        assert result.like_count == 100
        assert result.comment_count == 50
        assert result.thumbnail_url == "https://example.com/thumb.jpg"

    @patch("opencode.core.youtube.channel.GOOGLE_API_AVAILABLE", True)
    @patch("opencode.core.youtube.channel.build")
    def test_get_video_info_not_found(self, mock_build):
        """Test get_video_info raises when not found."""
        from opencode.core.youtube.channel import YouTubeChannelIndexer
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_youtube.videos().list().execute.return_value = {"items": []}
        mock_extractor = MagicMock()
        mock_chunker = MagicMock()

        indexer = YouTubeChannelIndexer(
            api_key="test_key",
            transcript_extractor=mock_extractor,
            chunker=mock_chunker,
        )
        with pytest.raises(ValueError, match="Video not found"):
            indexer.get_video_info("nonexistent")

    @patch("opencode.core.youtube.channel.GOOGLE_API_AVAILABLE", True)
    @patch("opencode.core.youtube.channel.build")
    def test_index_channel_with_id(self, mock_build):
        """Test index_channel with channel ID."""
        from opencode.core.youtube.channel import YouTubeChannelIndexer
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube

        # Mock channel info
        mock_youtube.channels().list().execute.return_value = {
            "items": [{
                "snippet": {"title": "Test", "description": ""},
                "statistics": {"subscriberCount": "0", "videoCount": "1", "viewCount": "0"},
                "contentDetails": {"relatedPlaylists": {"uploads": "UU123"}},
            }]
        }

        # Mock playlist items
        mock_youtube.playlistItems().list().execute.return_value = {
            "items": [{"contentDetails": {"videoId": "video1"}}],
            "nextPageToken": None,
        }

        # Mock video info
        mock_youtube.videos().list().execute.return_value = {
            "items": [{
                "snippet": {
                    "title": "Test Video",
                    "description": "A test",
                    "publishedAt": "2024-01-01T00:00:00Z",
                    "thumbnails": {},
                },
                "statistics": {"viewCount": "0", "likeCount": "0", "commentCount": "0"},
                "contentDetails": {"duration": "PT1M"},
            }]
        }

        # Mock transcript extractor
        mock_extractor = MagicMock()
        mock_transcript = MagicMock()
        mock_transcript.title = ""
        mock_transcript.author = ""
        mock_extractor.fetch_transcript_with_fallback.return_value = mock_transcript

        # Mock chunker
        mock_chunker = MagicMock()
        mock_chunk = MagicMock()
        mock_chunk.metadata = {}
        mock_chunker.chunk.return_value = [mock_chunk]

        indexer = YouTubeChannelIndexer(
            api_key="test_key",
            transcript_extractor=mock_extractor,
            chunker=mock_chunker,
        )
        result = indexer.index_channel("UC12345678901234567890", max_videos=1)

        assert len(result) == 1

    @patch("opencode.core.youtube.channel.GOOGLE_API_AVAILABLE", True)
    @patch("opencode.core.youtube.channel.build")
    def test_index_channel_incremental(self, mock_build):
        """Test index_channel with incremental indexing."""
        from opencode.core.youtube.channel import YouTubeChannelIndexer
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube

        # Mock channel info
        mock_youtube.channels().list().execute.return_value = {
            "items": [{
                "snippet": {"title": "Test", "description": ""},
                "statistics": {"subscriberCount": "0", "videoCount": "2", "viewCount": "0"},
                "contentDetails": {"relatedPlaylists": {"uploads": "UU123"}},
            }]
        }

        # Mock playlist items
        mock_youtube.playlistItems().list().execute.return_value = {
            "items": [
                {"contentDetails": {"videoId": "video1"}},
                {"contentDetails": {"videoId": "video2"}},
            ],
            "nextPageToken": None,
        }
        mock_extractor = MagicMock()
        mock_chunker = MagicMock()

        indexer = YouTubeChannelIndexer(
            api_key="test_key",
            transcript_extractor=mock_extractor,
            chunker=mock_chunker,
        )
        result = indexer.index_channel(
            "UC12345678901234567890",
            incremental=True,
            already_indexed={"video1"},
        )

        # Should skip video1, but since we mock everything, it will try video2
        # and fail gracefully

    @pytest.mark.asyncio
    @patch("opencode.core.youtube.channel.GOOGLE_API_AVAILABLE", True)
    @patch("opencode.core.youtube.channel.build")
    async def test_index_channel_async(self, mock_build):
        """Test index_channel_async."""
        from opencode.core.youtube.channel import YouTubeChannelIndexer
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube

        # Mock channel info
        mock_youtube.channels().list().execute.return_value = {
            "items": [{
                "snippet": {"title": "Test", "description": ""},
                "statistics": {"subscriberCount": "0", "videoCount": "0", "viewCount": "0"},
                "contentDetails": {"relatedPlaylists": {"uploads": "UU123"}},
            }]
        }

        # Mock playlist items (empty)
        mock_youtube.playlistItems().list().execute.return_value = {
            "items": [],
            "nextPageToken": None,
        }
        mock_extractor = MagicMock()
        mock_chunker = MagicMock()

        indexer = YouTubeChannelIndexer(
            api_key="test_key",
            transcript_extractor=mock_extractor,
            chunker=mock_chunker,
        )
        result = await indexer.index_channel_async("UC12345678901234567890")

        assert result == []

    @patch("opencode.core.youtube.channel.GOOGLE_API_AVAILABLE", True)
    @patch("opencode.core.youtube.channel.build")
    def test_get_channel_stats(self, mock_build):
        """Test get_channel_stats."""
        from opencode.core.youtube.channel import YouTubeChannelIndexer
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_youtube.channels().list().execute.return_value = {
            "items": [{
                "snippet": {"title": "Test Channel", "description": ""},
                "statistics": {"subscriberCount": "1000", "videoCount": "50", "viewCount": "10000"},
                "contentDetails": {"relatedPlaylists": {"uploads": "UU123"}},
            }]
        }
        mock_extractor = MagicMock()
        mock_chunker = MagicMock()

        indexer = YouTubeChannelIndexer(
            api_key="test_key",
            transcript_extractor=mock_extractor,
            chunker=mock_chunker,
        )
        result = indexer.get_channel_stats("UC12345678901234567890", indexed_videos=10, total_chunks=100)

        assert result.channel_id == "UC12345678901234567890"
        assert result.channel_title == "Test Channel"
        assert result.total_videos == 50
        assert result.indexed_videos == 10
        assert result.total_chunks == 100


@pytest.mark.unit
class TestYouTubeChannelIndexerNoGoogleAPI:
    """Tests for YouTubeChannelIndexer when Google API is not available."""

    @patch("opencode.core.youtube.channel.GOOGLE_API_AVAILABLE", False)
    def test_init_without_google_api(self):
        """Test initialization fails without Google API."""
        from opencode.core.youtube.channel import YouTubeChannelIndexer
        with pytest.raises(ImportError, match="google-api-python-client is not installed"):
            YouTubeChannelIndexer(api_key="test_key")
