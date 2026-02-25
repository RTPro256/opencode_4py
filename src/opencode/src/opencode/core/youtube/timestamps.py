"""
Timestamped YouTube Results

Provides functionality to generate timestamped YouTube links for
search results, allowing users to jump directly to relevant moments.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import urllib.parse


class TimestampedResult(BaseModel):
    """A search result with YouTube timestamp information"""
    text: str = Field(..., description="The transcript text")
    start_time: float = Field(..., description="Start time in seconds")
    duration: float = Field(..., description="Duration in seconds")
    video_id: str = Field(..., description="YouTube video ID")
    youtube_url: str = Field(..., description="Direct YouTube link with timestamp")
    end_time: float = Field(..., description="End time in seconds")
    relevance_score: Optional[float] = Field(None, description="Relevance score from search")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @property
    def timestamp_str(self) -> str:
        """Human-readable timestamp (MM:SS or HH:MM:SS)"""
        return self._format_timestamp(self.start_time)
    
    @property
    def duration_str(self) -> str:
        """Human-readable duration"""
        return self._format_timestamp(self.duration)
    
    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Format seconds as MM:SS or HH:MM:SS"""
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:d}:{secs:02d}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "text": self.text,
            "start_time": self.start_time,
            "duration": self.duration,
            "video_id": self.video_id,
            "youtube_url": self.youtube_url,
            "end_time": self.end_time,
            "timestamp": self.timestamp_str,
            "relevance_score": self.relevance_score,
            "metadata": self.metadata,
        }


class TimestampGenerator:
    """
    Generate timestamped YouTube URLs for search results.
    
    Creates direct links to specific moments in videos, making it
    easy for users to jump to relevant content.
    """
    
    # YouTube URL formats
    WATCH_URL_FORMAT = "https://www.youtube.com/watch?v={video_id}&t={seconds}s"
    SHORT_URL_FORMAT = "https://youtu.be/{video_id}?t={seconds}s"
    EMBED_URL_FORMAT = "https://www.youtube.com/embed/{video_id}?start={seconds}"
    
    def __init__(
        self,
        url_format: str = "watch",
        include_end_time: bool = False,
    ):
        """
        Initialize the timestamp generator.
        
        Args:
            url_format: URL format to use ("watch", "short", or "embed")
            include_end_time: Whether to include end time in metadata
        """
        self.url_format = url_format
        self.include_end_time = include_end_time
    
    def create_timestamp_url(
        self,
        video_id: str,
        start_time: float,
    ) -> str:
        """
        Create a YouTube URL with timestamp.
        
        Args:
            video_id: YouTube video ID
            start_time: Start time in seconds
            
        Returns:
            YouTube URL with timestamp parameter
        """
        seconds = int(start_time)
        
        if self.url_format == "short":
            return self.SHORT_URL_FORMAT.format(video_id=video_id, seconds=seconds)
        elif self.url_format == "embed":
            return self.EMBED_URL_FORMAT.format(video_id=video_id, seconds=seconds)
        else:
            return self.WATCH_URL_FORMAT.format(video_id=video_id, seconds=seconds)
    
    def create_result(
        self,
        text: str,
        start_time: float,
        duration: float,
        video_id: str,
        relevance_score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TimestampedResult:
        """
        Create a timestamped result from search data.
        
        Args:
            text: Transcript text
            start_time: Start time in seconds
            duration: Duration in seconds
            video_id: YouTube video ID
            relevance_score: Optional relevance score
            metadata: Additional metadata
            
        Returns:
            TimestampedResult with YouTube URL
        """
        youtube_url = self.create_timestamp_url(video_id, start_time)
        
        return TimestampedResult(
            text=text,
            start_time=start_time,
            duration=duration,
            video_id=video_id,
            youtube_url=youtube_url,
            end_time=start_time + duration,
            relevance_score=relevance_score,
            metadata=metadata or {},
        )
    
    def format_results(
        self,
        results: List[Dict[str, Any]],
        video_id: str,
    ) -> List[TimestampedResult]:
        """
        Add timestamped URLs to search results.
        
        Args:
            results: List of search result dictionaries
            video_id: YouTube video ID
            
        Returns:
            List of TimestampedResult objects
        """
        formatted = []
        
        for result in results:
            text = result.get("text", "")
            start = result.get("start", 0.0)
            duration = result.get("duration", 0.0)
            score = result.get("score") or result.get("relevance_score")
            metadata = result.get("metadata", {})
            
            formatted.append(self.create_result(
                text=text,
                start_time=start,
                duration=duration,
                video_id=video_id,
                relevance_score=score,
                metadata=metadata,
            ))
        
        return formatted
    
    def create_playlist_url(
        self,
        video_id: str,
        start_time: float,
        end_time: float,
    ) -> str:
        """
        Create a URL that plays a specific segment.
        
        Note: YouTube doesn't natively support end times in URLs,
        but this creates a URL starting at the specified time.
        
        Args:
            video_id: YouTube video ID
            start_time: Start time in seconds
            end_time: End time in seconds (for reference)
            
        Returns:
            YouTube URL starting at the specified time
        """
        return self.create_timestamp_url(video_id, start_time)
    
    def create_clip_url(
        self,
        video_id: str,
        start_time: float,
        end_time: float,
    ) -> str:
        """
        Create a YouTube clip URL (if supported).
        
        Args:
            video_id: YouTube video ID
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            YouTube clip URL or regular timestamped URL
        """
        # YouTube clips require a different format, but we can
        # at least provide a timestamped URL
        return self.create_timestamp_url(video_id, start_time)
    
    @staticmethod
    def parse_timestamp(timestamp_str: str) -> float:
        """
        Parse a timestamp string to seconds.
        
        Supports formats: "SS", "MM:SS", "HH:MM:SS"
        
        Args:
            timestamp_str: Timestamp string
            
        Returns:
            Time in seconds
        """
        parts = timestamp_str.split(":")
        
        if len(parts) == 1:
            return float(parts[0])
        elif len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
        elif len(parts) == 3:
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
        else:
            raise ValueError(f"Invalid timestamp format: {timestamp_str}")
    
    @staticmethod
    def extract_timestamp_from_url(url: str) -> Optional[int]:
        """
        Extract timestamp from a YouTube URL.
        
        Args:
            url: YouTube URL
            
        Returns:
            Timestamp in seconds or None
        """
        # Check for t= parameter
        if "t=" in url:
            try:
                # Parse URL and extract t parameter
                parsed = urllib.parse.urlparse(url)
                query = urllib.parse.parse_qs(parsed.query)
                
                if "t" in query:
                    t_value = query["t"][0]
                    # Remove 's' suffix if present
                    if t_value.endswith("s"):
                        t_value = t_value[:-1]
                    return int(t_value)
            except Exception:
                pass
        
        return None
