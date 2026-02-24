"""
YouTube Channel Indexing

Provides functionality to index entire YouTube channels for RAG,
enabling persona-based chatbots that understand a creator's content.
"""

import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio

from .transcript import YouTubeTranscriptExtractor, VideoTranscript
from .chunking import TranscriptChunker, ChunkingConfig, ChunkedTranscript

logger = logging.getLogger(__name__)

# Try to import Google API client
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    build = None
    HttpError = Exception


class ChannelStats(BaseModel):
    """Statistics for an indexed channel"""
    channel_id: str = Field(..., description="YouTube channel ID")
    channel_title: str = Field(..., description="Channel name")
    total_videos: int = Field(0, description="Total videos in channel")
    indexed_videos: int = Field(0, description="Number of indexed videos")
    total_chunks: int = Field(0, description="Total transcript chunks")
    total_duration_seconds: float = Field(0, description="Total video duration")
    last_indexed: Optional[datetime] = Field(None, description="Last indexing timestamp")
    languages: List[str] = Field(default_factory=list, description="Detected languages")
    
    @property
    def total_duration_hours(self) -> float:
        """Total duration in hours"""
        return self.total_duration_seconds / 3600
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "channel_id": self.channel_id,
            "channel_title": self.channel_title,
            "total_videos": self.total_videos,
            "indexed_videos": self.indexed_videos,
            "total_chunks": self.total_chunks,
            "total_duration_seconds": self.total_duration_seconds,
            "total_duration_hours": self.total_duration_hours,
            "last_indexed": self.last_indexed.isoformat() if self.last_indexed else None,
            "languages": self.languages,
        }


class VideoInfo(BaseModel):
    """Information about a YouTube video"""
    video_id: str = Field(..., description="YouTube video ID")
    title: str = Field(..., description="Video title")
    description: str = Field("", description="Video description")
    published_at: Optional[datetime] = Field(None, description="Publish date")
    duration: str = Field("", description="Duration string (ISO 8601)")
    view_count: int = Field(0, description="View count")
    like_count: int = Field(0, description="Like count")
    comment_count: int = Field(0, description="Comment count")
    thumbnail_url: str = Field("", description="Thumbnail URL")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "video_id": self.video_id,
            "title": self.title,
            "description": self.description,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "duration": self.duration,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "thumbnail_url": self.thumbnail_url,
        }


class YouTubeChannelIndexer:
    """
    Index entire YouTube channels for RAG.
    
    This class provides functionality to:
    - Fetch all video IDs from a channel
    - Download transcripts for each video
    - Process and chunk transcripts
    - Store in a vector database for RAG
    
    Inspired by balmasi-youtube-rag's channel persona approach.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        transcript_extractor: Optional[YouTubeTranscriptExtractor] = None,
        chunker: Optional[TranscriptChunker] = None,
    ):
        """
        Initialize the channel indexer.
        
        Args:
            api_key: YouTube Data API key
            transcript_extractor: Custom transcript extractor
            chunker: Custom transcript chunker
        """
        if not GOOGLE_API_AVAILABLE:
            raise ImportError(
                "google-api-python-client is not installed. "
                "Install it with: pip install google-api-python-client"
            )
        
        self.api_key = api_key
        self.youtube = None
        self.transcript_extractor = transcript_extractor or YouTubeTranscriptExtractor()
        self.chunker = chunker or TranscriptChunker()
    
    def _get_youtube_client(self):
        """Get or create YouTube API client"""
        if self.youtube is None:
            if not self.api_key:
                raise ValueError("YouTube API key is required")
            self.youtube = build("youtube", "v3", developerKey=self.api_key)
        return self.youtube
    
    def get_channel_id(self, channel_handle: str) -> str:
        """
        Get channel ID from handle (e.g., @channelname).
        
        Args:
            channel_handle: Channel handle (with or without @)
            
        Returns:
            Channel ID
        """
        youtube = self._get_youtube_client()
        
        # Remove @ if present
        handle = channel_handle.lstrip("@")
        
        try:
            # Search for channel
            response = youtube.search().list(
                part="snippet",
                q=handle,
                type="channel",
                maxResults=1,
            ).execute()
            
            if response.get("items"):
                return response["items"][0]["snippet"]["channelId"]
            
            raise ValueError(f"Channel not found: {channel_handle}")
            
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            raise
    
    def get_channel_info(self, channel_id: str) -> Dict[str, Any]:
        """
        Get channel information.
        
        Args:
            channel_id: YouTube channel ID
            
        Returns:
            Channel information dictionary
        """
        youtube = self._get_youtube_client()
        
        try:
            response = youtube.channels().list(
                part="snippet,statistics,contentDetails",
                id=channel_id,
            ).execute()
            
            if response.get("items"):
                item = response["items"][0]
                return {
                    "channel_id": channel_id,
                    "title": item["snippet"]["title"],
                    "description": item["snippet"]["description"],
                    "subscriber_count": int(item["statistics"].get("subscriberCount", 0)),
                    "video_count": int(item["statistics"].get("videoCount", 0)),
                    "view_count": int(item["statistics"].get("viewCount", 0)),
                    "uploads_playlist_id": item["contentDetails"]["relatedPlaylists"]["uploads"],
                }
            
            raise ValueError(f"Channel not found: {channel_id}")
            
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            raise
    
    def get_video_ids(
        self,
        channel_id: str,
        max_videos: Optional[int] = None,
    ) -> List[str]:
        """
        Get all video IDs from a channel.
        
        Args:
            channel_id: YouTube channel ID
            max_videos: Maximum number of videos to fetch
            
        Returns:
            List of video IDs
        """
        youtube = self._get_youtube_client()
        
        # Get uploads playlist ID
        channel_info = self.get_channel_info(channel_id)
        playlist_id = channel_info["uploads_playlist_id"]
        
        video_ids = []
        next_page_token = None
        
        while True:
            try:
                response = youtube.playlistItems().list(
                    part="contentDetails",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token,
                ).execute()
                
                for item in response.get("items", []):
                    video_ids.append(item["contentDetails"]["videoId"])
                    
                    if max_videos and len(video_ids) >= max_videos:
                        return video_ids[:max_videos]
                
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break
                    
            except HttpError as e:
                logger.error(f"YouTube API error: {e}")
                break
        
        return video_ids
    
    def get_video_info(self, video_id: str) -> VideoInfo:
        """
        Get detailed information about a video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            VideoInfo object
        """
        youtube = self._get_youtube_client()
        
        try:
            response = youtube.videos().list(
                part="snippet,statistics,contentDetails",
                id=video_id,
            ).execute()
            
            if response.get("items"):
                item = response["items"][0]
                snippet = item["snippet"]
                stats = item["statistics"]
                content = item["contentDetails"]
                
                return VideoInfo(
                    video_id=video_id,
                    title=snippet.get("title", ""),
                    description=snippet.get("description", ""),
                    published_at=datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00")) if snippet.get("publishedAt") else None,
                    duration=content.get("duration", ""),
                    view_count=int(stats.get("viewCount", 0)),
                    like_count=int(stats.get("likeCount", 0)),
                    comment_count=int(stats.get("commentCount", 0)),
                    thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                )
            
            raise ValueError(f"Video not found: {video_id}")
            
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            raise
    
    def index_channel(
        self,
        channel_handle_or_id: str,
        max_videos: Optional[int] = None,
        incremental: bool = True,
        already_indexed: Optional[set] = None,
    ) -> List[ChunkedTranscript]:
        """
        Index all videos from a channel.
        
        Args:
            channel_handle_or_id: Channel handle or ID
            max_videos: Maximum videos to index
            incremental: Skip already indexed videos
            already_indexed: Set of already indexed video IDs
            
        Returns:
            List of chunked transcripts
        """
        # Get channel ID
        if channel_handle_or_id.startswith("@") or len(channel_handle_or_id) < 20:
            channel_id = self.get_channel_id(channel_handle_or_id)
        else:
            channel_id = channel_handle_or_id
        
        # Get video IDs
        video_ids = self.get_video_ids(channel_id, max_videos)
        logger.info(f"Found {len(video_ids)} videos for channel {channel_id}")
        
        # Filter already indexed
        if incremental and already_indexed:
            video_ids = [vid for vid in video_ids if vid not in already_indexed]
            logger.info(f"Indexing {len(video_ids)} new videos")
        
        # Process videos
        all_chunks = []
        
        for i, video_id in enumerate(video_ids):
            try:
                logger.info(f"Processing video {i+1}/{len(video_ids)}: {video_id}")
                
                # Get video info
                video_info = self.get_video_info(video_id)
                
                # Get transcript
                transcript = self.transcript_extractor.fetch_transcript_with_fallback(video_id)
                transcript.title = video_info.title
                transcript.author = video_info.title  # Use video title as fallback
                
                # Chunk transcript
                chunks = self.chunker.chunk(transcript)
                
                # Add video metadata to chunks
                for chunk in chunks:
                    chunk.metadata.update({
                        "video_title": video_info.title,
                        "video_description": video_info.description[:500] if video_info.description else "",
                        "view_count": video_info.view_count,
                        "published_at": video_info.published_at.isoformat() if video_info.published_at else None,
                    })
                
                all_chunks.extend(chunks)
                
            except Exception as e:
                logger.warning(f"Failed to process video {video_id}: {e}")
                continue
        
        return all_chunks
    
    async def index_channel_async(
        self,
        channel_handle_or_id: str,
        max_videos: Optional[int] = None,
        incremental: bool = True,
        already_indexed: Optional[set] = None,
    ) -> List[ChunkedTranscript]:
        """
        Async wrapper for channel indexing.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.index_channel(
                channel_handle_or_id,
                max_videos,
                incremental,
                already_indexed,
            ),
        )
    
    def get_channel_stats(
        self,
        channel_handle_or_id: str,
        indexed_videos: int = 0,
        total_chunks: int = 0,
    ) -> ChannelStats:
        """
        Get statistics for a channel.
        
        Args:
            channel_handle_or_id: Channel handle or ID
            indexed_videos: Number of indexed videos
            total_chunks: Total chunks created
            
        Returns:
            ChannelStats object
        """
        # Get channel ID
        if channel_handle_or_id.startswith("@") or len(channel_handle_or_id) < 20:
            channel_id = self.get_channel_id(channel_handle_or_id)
        else:
            channel_id = channel_handle_or_id
        
        # Get channel info
        info = self.get_channel_info(channel_id)
        
        return ChannelStats(
            channel_id=channel_id,
            channel_title=info["title"],
            total_videos=info["video_count"],
            indexed_videos=indexed_videos,
            total_chunks=total_chunks,
            total_duration_seconds=0.0,  # Would need to sum from indexed videos
            last_indexed=datetime.now() if indexed_videos > 0 else None,
        )
