"""
Video Processing Module

Provides functionality for multimodal video processing:
- Frame extraction
- Audio extraction
- Transcription
"""

from .frames import FrameExtractor, ExtractedFrame
from .audio import AudioExtractor, AudioTranscriber

__all__ = [
    "FrameExtractor",
    "ExtractedFrame",
    "AudioExtractor",
    "AudioTranscriber",
]
