"""
YouTube Transcript Extraction

Provides functionality to fetch and process YouTube video transcripts.
Supports multiple languages and automatic fallback.
"""

import re
import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Try to import youtube-transcript-api
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        TranscriptsDisabled,
        NoTranscriptFound,
        VideoUnavailable,
        TooManyRequests,
        NoTranscriptAvailable,
    )
    YOUTUBE_TRANSCRIPT_API_AVAILABLE = True
except ImportError:
    YOUTUBE_TRANSCRIPT_API_AVAILABLE = False
    YouTubeTranscriptApi = None
    TranscriptsDisabled = Exception
    NoTranscriptFound = Exception
    VideoUnavailable = Exception
    TooManyRequests = Exception
    NoTranscriptAvailable = Exception


class TranscriptChunk(BaseModel):
    """A single transcript chunk with timing information"""
    text: str = Field(..., description="The transcript text")
    start: float = Field(..., description="Start time in seconds")
    duration: float = Field(..., description="Duration in seconds")
    
    @property
    def end(self) -> float:
        """End time in seconds"""
        return self.start + self.duration
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "text": self.text,
            "start": self.start,
            "duration": self.duration,
        }


class VideoTranscript(BaseModel):
    """Complete video transcript with metadata"""
    video_id: str = Field(..., description="YouTube video ID")
    title: Optional[str] = Field(None, description="Video title")
    author: Optional[str] = Field(None, description="Channel/author name")
    chunks: List[TranscriptChunk] = Field(default_factory=list, description="Transcript chunks")
    language: str = Field("en", description="Transcript language")
    
    @property
    def full_text(self) -> str:
        """Get complete transcript as single text"""
        return " ".join(chunk.text for chunk in self.chunks)
    
    @property
    def total_duration(self) -> float:
        """Total video duration in seconds"""
        if not self.chunks:
            return 0.0
        return max(chunk.end for chunk in self.chunks)
    
    def get_chunk_at_time(self, timestamp: float) -> Optional[TranscriptChunk]:
        """Get the chunk at a specific timestamp"""
        for chunk in self.chunks:
            if chunk.start <= timestamp <= chunk.end:
                return chunk
        return None


class YouTubeTranscriptExtractor:
    """
    Extract transcripts from YouTube videos.
    
    Features:
    - Multiple URL format support
    - Language preference with fallback
    - Proxy support
    - Error handling with detailed messages
    """
    
    # URL patterns for extracting video IDs
    URL_PATTERNS = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"(?:embed\/)([0-9A-Za-z_-]{11})",
        r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})",
        r"(?:shorts\/)([0-9A-Za-z_-]{11})",
    ]
    
    def __init__(
        self,
        preferred_languages: Optional[List[str]] = None,
        preserve_formatting: bool = False,
        proxy: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize the transcript extractor.
        
        Args:
            preferred_languages: List of preferred language codes (e.g., ["en", "es"])
            preserve_formatting: Whether to preserve HTML formatting in transcripts
            proxy: Proxy configuration for requests
        """
        if not YOUTUBE_TRANSCRIPT_API_AVAILABLE:
            raise ImportError(
                "youtube-transcript-api is not installed. "
                "Install it with: pip install youtube-transcript-api"
            )
        
        self.preferred_languages = preferred_languages or ["en"]
        self.preserve_formatting = preserve_formatting
        self.proxy = proxy
    
    def extract_video_id(self, url: str) -> str:
        """
        Extract video ID from various YouTube URL formats.
        
        Args:
            url: YouTube video URL
            
        Returns:
            11-character video ID
            
        Raises:
            ValueError: If URL is not a valid YouTube URL
        """
        for pattern in self.URL_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # Try as direct video ID
        if re.match(r"^[0-9A-Za-z_-]{11}$", url):
            return url
        
        raise ValueError(f"Invalid YouTube URL or video ID: {url}")
    
    def fetch_transcript(
        self,
        video_id_or_url: str,
        languages: Optional[List[str]] = None,
    ) -> VideoTranscript:
        """
        Fetch transcript for a YouTube video.
        
        Args:
            video_id_or_url: YouTube video ID or URL
            languages: Override preferred languages for this request
            
        Returns:
            VideoTranscript object with chunks and metadata
            
        Raises:
            TranscriptsDisabled: If transcripts are disabled for the video
            NoTranscriptFound: If no transcript is found in preferred languages
            VideoUnavailable: If the video is unavailable
        """
        video_id = self.extract_video_id(video_id_or_url)
        languages = languages or self.preferred_languages
        
        try:
            # Fetch transcript
            transcript_list = YouTubeTranscriptApi.get_transcript(
                video_id,
                languages=languages,
                preserve_formatting=self.preserve_formatting,
                proxies=self.proxy,
            )
            
            # Convert to chunks
            chunks = [
                TranscriptChunk(
                    text=item["text"],
                    start=item["start"],
                    duration=item["duration"],
                )
                for item in transcript_list
            ]
            
            # Detect language from first available transcript
            language = languages[0] if languages else "en"
            
            return VideoTranscript(
                video_id=video_id,
                chunks=chunks,
                language=language,
            )
            
        except TranscriptsDisabled:
            logger.warning(f"Transcripts disabled for video: {video_id}")
            raise
        except NoTranscriptFound:
            logger.warning(f"No transcript found for video {video_id} in languages: {languages}")
            raise
        except VideoUnavailable:
            logger.warning(f"Video unavailable: {video_id}")
            raise
        except TooManyRequests:
            logger.warning(f"Too many requests for video: {video_id}")
            raise
        except NoTranscriptAvailable:
            logger.warning(f"No transcript available for video: {video_id}")
            raise
    
    def fetch_transcript_with_fallback(
        self,
        video_id_or_url: str,
        fallback_languages: Optional[List[str]] = None,
    ) -> VideoTranscript:
        """
        Fetch transcript with automatic language fallback.
        
        Args:
            video_id_or_url: YouTube video ID or URL
            fallback_languages: Additional languages to try if preferred fails
            
        Returns:
            VideoTranscript object
        """
        video_id = self.extract_video_id(video_id_or_url)
        
        # Try preferred languages first
        try:
            return self.fetch_transcript(video_id)
        except NoTranscriptFound:
            pass
        
        # Try fallback languages
        if fallback_languages:
            for lang in fallback_languages:
                try:
                    return self.fetch_transcript(video_id, languages=[lang])
                except NoTranscriptFound:
                    continue
        
        # Try to get any available transcript
        try:
            return self.fetch_transcript(video_id, languages=[])
        except Exception as e:
            logger.error(f"Failed to fetch any transcript for {video_id}: {e}")
            raise
    
    def list_available_transcripts(self, video_id_or_url: str) -> List[Dict[str, Any]]:
        """
        List all available transcripts for a video.
        
        Args:
            video_id_or_url: YouTube video ID or URL
            
        Returns:
            List of available transcript info dictionaries
        """
        video_id = self.extract_video_id(video_id_or_url)
        
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            available = []
            for transcript in transcript_list:
                available.append({
                    "language": transcript.language,
                    "language_code": transcript.language_code,
                    "is_generated": transcript.is_generated,
                    "is_translatable": transcript.is_translatable,
                })
            
            return available
            
        except Exception as e:
            logger.error(f"Failed to list transcripts for {video_id}: {e}")
            return []
    
    async def fetch_transcript_async(
        self,
        video_id_or_url: str,
        languages: Optional[List[str]] = None,
    ) -> VideoTranscript:
        """
        Async wrapper for transcript fetching.
        
        Note: youtube-transcript-api is synchronous, so this runs in a thread.
        """
        import asyncio
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.fetch_transcript(video_id_or_url, languages),
        )
