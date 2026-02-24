"""
Video Frame Extraction

Provides functionality to extract frames from videos for multimodal RAG.
Supports various extraction strategies including fixed FPS and key frame detection.
"""

import os
import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)

# Try to import moviepy
try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    VideoFileClip = None


class ExtractedFrame(BaseModel):
    """Information about an extracted frame"""
    frame_path: str = Field(..., description="Path to the frame image")
    timestamp: float = Field(..., description="Timestamp in seconds")
    frame_number: int = Field(..., description="Frame number in sequence")
    width: int = Field(0, description="Frame width in pixels")
    height: int = Field(0, description="Frame height in pixels")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @property
    def timestamp_str(self) -> str:
        """Human-readable timestamp"""
        seconds = int(self.timestamp)
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "frame_path": self.frame_path,
            "timestamp": self.timestamp,
            "frame_number": self.frame_number,
            "width": self.width,
            "height": self.height,
            "timestamp_str": self.timestamp_str,
            "metadata": self.metadata,
        }


class FrameExtractor:
    """
    Extract frames from video files.
    
    Supports multiple extraction strategies:
    - Fixed FPS: Extract frames at regular intervals
    - Key frames: Extract frames at scene changes
    - Smart sampling: Extract frames based on content analysis
    """
    
    def __init__(
        self,
        fps: float = 0.5,
        output_format: str = "png",
        output_dir: str = "./frames",
        naming_pattern: str = "frame_%04d",
    ):
        """
        Initialize the frame extractor.
        
        Args:
            fps: Frames per second to extract (default 0.5 = 1 frame every 2 seconds)
            output_format: Image format (png, jpg)
            output_dir: Directory to save frames
            naming_pattern: Frame naming pattern with printf-style formatting
        """
        if not MOVIEPY_AVAILABLE:
            raise ImportError(
                "moviepy is not installed. "
                "Install it with: pip install moviepy"
            )
        
        self.fps = fps
        self.output_format = output_format
        self.output_dir = output_dir
        self.naming_pattern = naming_pattern
    
    def extract_frames(
        self,
        video_path: str,
        output_dir: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> List[ExtractedFrame]:
        """
        Extract frames from a video file.
        
        Args:
            video_path: Path to the video file
            output_dir: Override output directory
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            List of ExtractedFrame objects
        """
        output_dir = output_dir or self.output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        frames = []
        
        try:
            with VideoFileClip(video_path) as clip:
                # Apply time constraints
                if start_time is not None or end_time is not None:
                    clip = clip.subclip(
                        start_time or 0,
                        end_time if end_time else clip.duration,
                    )
                
                # Calculate frame times
                duration = clip.duration
                interval = 1.0 / self.fps
                frame_times = []
                t = 0.0
                while t < duration:
                    frame_times.append(t)
                    t += interval
                
                # Extract frames
                for i, t in enumerate(frame_times):
                    frame_name = f"{self.naming_pattern}.{self.output_format}" % (i + 1)
                    frame_path = os.path.join(output_dir, frame_name)
                    
                    # Save frame
                    clip.save_frame(frame_path, t)
                    
                    # Get frame dimensions
                    frame = ExtractedFrame(
                        frame_path=frame_path,
                        timestamp=t,
                        frame_number=i + 1,
                        width=clip.w,
                        height=clip.h,
                        metadata={
                            "video_path": video_path,
                            "fps": self.fps,
                        },
                    )
                    frames.append(frame)
                    
                    if (i + 1) % 10 == 0:
                        logger.info(f"Extracted {i + 1} frames...")
                
                logger.info(f"Total frames extracted: {len(frames)}")
                
        except Exception as e:
            logger.error(f"Error extracting frames: {e}")
            raise
        
        return frames
    
    def extract_key_frames(
        self,
        video_path: str,
        output_dir: Optional[str] = None,
        threshold: float = 0.3,
    ) -> List[ExtractedFrame]:
        """
        Extract key frames based on scene changes.
        
        This is a simplified implementation that extracts frames at
        regular intervals. A full implementation would use scene
        detection algorithms.
        
        Args:
            video_path: Path to the video file
            output_dir: Override output directory
            threshold: Scene change threshold (not used in this implementation)
            
        Returns:
            List of ExtractedFrame objects
        """
        # For now, use regular extraction
        # A full implementation would use ffmpeg or similar for scene detection
        return self.extract_frames(video_path, output_dir)
    
    def extract_frames_at_timestamps(
        self,
        video_path: str,
        timestamps: List[float],
        output_dir: Optional[str] = None,
    ) -> List[ExtractedFrame]:
        """
        Extract frames at specific timestamps.
        
        Args:
            video_path: Path to the video file
            timestamps: List of timestamps in seconds
            output_dir: Override output directory
            
        Returns:
            List of ExtractedFrame objects
        """
        output_dir = output_dir or self.output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        frames = []
        
        try:
            with VideoFileClip(video_path) as clip:
                for i, t in enumerate(timestamps):
                    if t < 0 or t >= clip.duration:
                        logger.warning(f"Timestamp {t} out of range, skipping")
                        continue
                    
                    frame_name = f"{self.naming_pattern}.{self.output_format}" % (i + 1)
                    frame_path = os.path.join(output_dir, frame_name)
                    
                    clip.save_frame(frame_path, t)
                    
                    frame = ExtractedFrame(
                        frame_path=frame_path,
                        timestamp=t,
                        frame_number=i + 1,
                        width=clip.w,
                        height=clip.h,
                        metadata={
                            "video_path": video_path,
                        },
                    )
                    frames.append(frame)
                    
        except Exception as e:
            logger.error(f"Error extracting frames at timestamps: {e}")
            raise
        
        return frames
    
    async def extract_frames_async(
        self,
        video_path: str,
        output_dir: Optional[str] = None,
    ) -> List[ExtractedFrame]:
        """
        Async wrapper for frame extraction.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.extract_frames(video_path, output_dir),
        )
    
    @staticmethod
    def get_video_info(video_path: str) -> Dict[str, Any]:
        """
        Get information about a video file.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary with video information
        """
        if not MOVIEPY_AVAILABLE:
            raise ImportError("moviepy is not installed")
        
        with VideoFileClip(video_path) as clip:
            return {
                "duration": clip.duration,
                "fps": clip.fps,
                "width": clip.w,
                "height": clip.h,
                "size": clip.size,
                "has_audio": clip.audio is not None,
            }
