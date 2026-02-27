"""
YouTube Transcript Tool - Fetch and process YouTube video transcripts.

Based on youtube_Rag project implementation.
"""

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .base import Tool, ToolResult


class TranscriptChunk(BaseModel):
    """A single transcript chunk with timing information."""
    text: str
    """Transcript text."""
    
    start: float
    """Start time in seconds."""
    
    duration: float
    """Duration in seconds."""
    
    def to_timestamp_url(self, video_id: str) -> str:
        """Generate a YouTube URL with timestamp.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            URL with timestamp
        """
        minutes = int(self.start // 60)
        seconds = int(self.start % 60)
        return f"https://youtube.com/watch?v={video_id}&t={minutes}m{seconds}s"
    
    def format_timestamp(self) -> str:
        """Format start time as MM:SS.
        
        Returns:
            Formatted timestamp
        """
        minutes = int(self.start // 60)
        seconds = int(self.start % 60)
        return f"{minutes}:{seconds:02d}"


class VideoInfo(BaseModel):
    """Video information."""
    video_id: str
    """YouTube video ID."""
    
    title: Optional[str] = None
    """Video title if available."""
    
    duration: Optional[float] = None
    """Total duration in seconds."""
    
    language: str = "en"
    """Transcript language."""


class YouTubeTranscriptTool(Tool):
    """Fetch and process YouTube video transcripts.
    
    Provides functionality to:
    - Fetch transcripts from YouTube videos
    - Process and chunk transcripts
    - Generate summaries
    - Create timestamped references
    
    Requires youtube-transcript-api package.
    """
    
    @property
    def name(self) -> str:
        return "youtube_transcript"
    
    @property
    def description(self) -> str:
        return "Fetch transcript from a YouTube video for analysis and Q&A"
    
    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "YouTube video URL"
                },
                "language": {
                    "type": "string",
                    "default": "en",
                    "description": "Preferred transcript language"
                },
                "chunk_size": {
                    "type": "integer",
                    "default": 6,
                    "description": "Number of transcript segments to merge per chunk"
                },
                "include_timestamps": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include timestamp information in output"
                }
            },
            "required": ["url"]
        }
    
    # URL patterns for extracting video ID
    URL_PATTERNS = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"(?:embed\/)([0-9A-Za-z_-]{11})",
        r"(?:youtu\.be\/)([0-9A-Za-z_-]{11})",
        r"(?:shorts\/)([0-9A-Za-z_-]{11})",
    ]
    
    async def execute(self, **params: Any) -> ToolResult:
        """Execute the YouTube transcript tool.
        
        Args:
            **params: Tool parameters including url, language, chunk_size, include_timestamps
            
        Returns:
            ToolResult with transcript data
        """
        url = params.get("url", "")
        language = params.get("language", "en")
        chunk_size = params.get("chunk_size", 6)
        include_timestamps = params.get("include_timestamps", True)
        
        try:
            # Extract video ID
            video_id = self._extract_video_id(url)
            if not video_id:
                return ToolResult.err(
                    error="Could not extract video ID from URL",
                    output=f"Invalid YouTube URL: {url}"
                )
            
            # Fetch transcript
            transcript = await self._fetch_transcript(video_id, language)
            if not transcript:
                return ToolResult.err(
                    error="Transcript not available",
                    output=f"Could not fetch transcript for video: {video_id}"
                )
            
            # Process transcript
            chunks = self._merge_chunks(transcript, chunk_size)
            full_text = " ".join(chunk.text for chunk in chunks)
            
            # Build output
            output_lines = [f"Transcript for video: {video_id}"]
            output_lines.append(f"Total chunks: {len(chunks)}")
            output_lines.append(f"Total duration: {chunks[-1].start + chunks[-1].duration:.1f}s")
            output_lines.append("")
            
            if include_timestamps:
                for chunk in chunks[:20]:  # Limit output
                    output_lines.append(f"[{chunk.format_timestamp()}] {chunk.text}")
                if len(chunks) > 20:
                    output_lines.append(f"... and {len(chunks) - 20} more chunks")
            else:
                output_lines.append(full_text[:2000])
                if len(full_text) > 2000:
                    output_lines.append("... (truncated)")
            
            return ToolResult.ok(
                output="\n".join(output_lines),
                metadata={
                    "video_id": video_id,
                    "video_info": {
                        "video_id": video_id,
                        "language": language,
                        "duration": chunks[-1].start + chunks[-1].duration if chunks else 0,
                    },
                    "transcript": [chunk.model_dump() for chunk in chunks],
                    "full_text": full_text,
                    "chunk_count": len(chunks),
                }
            )
            
        except ImportError:
            return ToolResult.err(
                error="Install with: pip install youtube-transcript-api",
                output="youtube-transcript-api package not installed"
            )
        except Exception as e:
            return ToolResult.err(
                error=str(e),
                output=f"Failed to fetch transcript: {str(e)}"
            )
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from various YouTube URL formats.
        
        Args:
            url: YouTube URL
            
        Returns:
            Video ID or None if not found
        """
        for pattern in self.URL_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    async def _fetch_transcript(
        self,
        video_id: str,
        language: str = "en"
    ) -> List[TranscriptChunk]:
        """Fetch transcript from YouTube.
        
        Args:
            video_id: YouTube video ID
            language: Preferred language
            
        Returns:
            List of transcript chunks
        """
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
        except ImportError:
            raise ImportError("youtube-transcript-api not installed")
        
        # Fetch transcript
        api = YouTubeTranscriptApi()
        transcript_list = api.fetch(video_id)
        
        # Convert to chunks
        chunks = []
        for item in transcript_list:
            chunks.append(TranscriptChunk(
                text=item.text.replace("\n", " ").strip(),
                start=item.start,
                duration=item.duration
            ))
        
        return chunks
    
    def _merge_chunks(
        self,
        transcript: List[TranscriptChunk],
        group_size: int = 6
    ) -> List[TranscriptChunk]:
        """Merge small chunks into larger context-preserving chunks.
        
        Args:
            transcript: List of transcript chunks
            group_size: Number of chunks to merge
            
        Returns:
            Merged chunks
        """
        if not transcript:
            return []
        
        merged = []
        total_chunks = len(transcript)
        num_groups = (total_chunks + group_size - 1) // group_size
        
        for i in range(num_groups):
            start_idx = i * group_size
            end_idx = min((i + 1) * group_size, total_chunks)
            
            group = transcript[start_idx:end_idx]
            
            # Merge text
            text = " ".join(chunk.text for chunk in group)
            
            # Calculate timing
            start = group[0].start
            duration = group[-1].start + group[-1].duration - start
            
            merged.append(TranscriptChunk(
                text=text,
                start=start,
                duration=duration
            ))
        
        return merged
    
    def get_video_url(self, video_id: str) -> str:
        """Get YouTube URL from video ID.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Full YouTube URL
        """
        return f"https://youtube.com/watch?v={video_id}"
