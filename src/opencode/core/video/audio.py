"""
Audio Extraction and Transcription

Provides functionality to extract audio from videos and transcribe it
using various speech recognition engines including Whisper.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)

# Try to import moviepy for audio extraction
try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    VideoFileClip = None

# Try to import speech recognition
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    sr = None


class TranscriptionSegment(BaseModel):
    """A segment of transcribed audio"""
    text: str = Field(..., description="Transcribed text")
    start_time: float = Field(0.0, description="Start time in seconds")
    end_time: float = Field(0.0, description="End time in seconds")
    confidence: float = Field(0.0, description="Confidence score (0-1)")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "text": self.text,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "confidence": self.confidence,
        }


class TranscriptionResult(BaseModel):
    """Complete transcription result"""
    text: str = Field(..., description="Full transcribed text")
    segments: List[TranscriptionSegment] = Field(
        default_factory=list,
        description="Individual transcription segments"
    )
    language: str = Field("en", description="Detected or specified language")
    duration: float = Field(0.0, description="Audio duration in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "text": self.text,
            "segments": [s.to_dict() for s in self.segments],
            "language": self.language,
            "duration": self.duration,
            "metadata": self.metadata,
        }


class AudioExtractor:
    """
    Extract audio from video files.
    
    Supports various audio formats and quality settings.
    """
    
    def __init__(
        self,
        output_format: str = "wav",
        sample_rate: int = 16000,
        channels: int = 1,
    ):
        """
        Initialize the audio extractor.
        
        Args:
            output_format: Audio format (wav, mp3, aac)
            sample_rate: Sample rate in Hz
            channels: Number of audio channels (1 = mono, 2 = stereo)
        """
        if not MOVIEPY_AVAILABLE:
            raise ImportError(
                "moviepy is not installed. "
                "Install it with: pip install moviepy"
            )
        
        self.output_format = output_format
        self.sample_rate = sample_rate
        self.channels = channels
    
    def extract_audio(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
    ) -> str:
        """
        Extract audio from a video file.
        
        Args:
            video_path: Path to the video file
            output_path: Path for the output audio file
            start_time: Start time in seconds
            end_time: End time in seconds
            
        Returns:
            Path to the extracted audio file
        """
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = f"{base_name}.{self.output_format}"
        
        try:
            with VideoFileClip(video_path) as clip:
                # Apply time constraints
                if start_time is not None or end_time is not None:
                    clip = clip.subclip(
                        start_time or 0,
                        end_time if end_time else clip.duration,
                    )
                
                if clip.audio is None:
                    raise ValueError(f"No audio track in video: {video_path}")
                
                # Extract audio
                clip.audio.write_audiofile(
                    output_path,
                    fps=self.sample_rate,
                    nbytes=2,  # 16-bit
                    codec=None,  # Auto-detect from extension
                )
                
                logger.info(f"Audio extracted to: {output_path}")
                return output_path
                
        except Exception as e:
            logger.error(f"Error extracting audio: {e}")
            raise
    
    async def extract_audio_async(
        self,
        video_path: str,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Async wrapper for audio extraction.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.extract_audio(video_path, output_path),
        )


class AudioTranscriber:
    """
    Transcribe audio files using various speech recognition engines.
    
    Supports:
    - OpenAI Whisper (local)
    - Google Speech Recognition
    - Sphinx (offline)
    """
    
    def __init__(
        self,
        engine: str = "whisper",
        language: str = "en-US",
        model: str = "base",
    ):
        """
        Initialize the transcriber.
        
        Args:
            engine: Recognition engine ("whisper", "google", "sphinx")
            language: Language code
            model: Whisper model size (tiny, base, small, medium, large)
        """
        if not SPEECH_RECOGNITION_AVAILABLE:
            raise ImportError(
                "SpeechRecognition is not installed. "
                "Install it with: pip install SpeechRecognition"
            )
        
        self.engine = engine
        self.language = language
        self.model = model
        self.recognizer = sr.Recognizer()
    
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        """
        Transcribe an audio file.
        
        Args:
            audio_path: Path to the audio file
            language: Override language code
            
        Returns:
            TranscriptionResult object
        """
        language = language or self.language
        
        try:
            with sr.AudioFile(audio_path) as source:
                audio_data = self.recognizer.record(source)
                
                if self.engine == "whisper":
                    return self._transcribe_whisper(audio_data, language)
                elif self.engine == "google":
                    return self._transcribe_google(audio_data, language)
                elif self.engine == "sphinx":
                    return self._transcribe_sphinx(audio_data)
                else:
                    raise ValueError(f"Unknown engine: {self.engine}")
                    
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            raise
    
    def _transcribe_whisper(
        self,
        audio_data: "sr.AudioData",
        language: str,
    ) -> TranscriptionResult:
        """Transcribe using OpenAI Whisper"""
        try:
            text = self.recognizer.recognize_whisper(
                audio_data,
                language=language.split("-")[0],  # Whisper uses 2-letter codes
                model=self.model,
            )
            
            return TranscriptionResult(
                text=text,
                segments=[TranscriptionSegment(text=text)],
                language=language,
                metadata={"engine": "whisper", "model": self.model},
            )
            
        except sr.UnknownValueError:
            logger.warning("Whisper could not understand audio")
            return TranscriptionResult(text="", language=language)
        except sr.RequestError as e:
            logger.error(f"Whisper error: {e}")
            raise
    
    def _transcribe_google(
        self,
        audio_data: "sr.AudioData",
        language: str,
    ) -> TranscriptionResult:
        """Transcribe using Google Speech Recognition"""
        try:
            text = self.recognizer.recognize_google(
                audio_data,
                language=language,
            )
            
            return TranscriptionResult(
                text=text,
                segments=[TranscriptionSegment(text=text)],
                language=language,
                metadata={"engine": "google"},
            )
            
        except sr.UnknownValueError:
            logger.warning("Google Speech Recognition could not understand audio")
            return TranscriptionResult(text="", language=language)
        except sr.RequestError as e:
            logger.error(f"Google Speech Recognition error: {e}")
            raise
    
    def _transcribe_sphinx(
        self,
        audio_data: "sr.AudioData",
    ) -> TranscriptionResult:
        """Transcribe using CMU Sphinx (offline)"""
        try:
            text = self.recognizer.recognize_sphinx(audio_data)
            
            return TranscriptionResult(
                text=text,
                segments=[TranscriptionSegment(text=text)],
                language="en-US",
                metadata={"engine": "sphinx"},
            )
            
        except sr.UnknownValueError:
            logger.warning("Sphinx could not understand audio")
            return TranscriptionResult(text="")
        except sr.RequestError as e:
            logger.error(f"Sphinx error: {e}")
            raise
    
    def transcribe_with_timestamps(
        self,
        audio_path: str,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        """
        Transcribe with word-level timestamps (Whisper only).
        
        Note: This requires the openai-whisper package for full support.
        The basic SpeechRecognition library doesn't provide timestamps.
        """
        # Try to use openai-whisper if available
        try:
            import whisper
            
            model = whisper.load_model(self.model)
            result = model.transcribe(audio_path, language=language or self.language)
            
            segments = []
            for segment in result.get("segments", []):
                segments.append(TranscriptionSegment(
                    text=segment["text"].strip(),
                    start_time=segment["start"],
                    end_time=segment["end"],
                    confidence=segment.get("avg_logprob", 0.0),
                ))
            
            return TranscriptionResult(
                text=result["text"],
                segments=segments,
                language=result.get("language", language or "en"),
                metadata={"engine": "whisper", "model": self.model},
            )
            
        except ImportError:
            logger.warning("openai-whisper not installed, falling back to basic transcription")
            return self.transcribe(audio_path, language)
    
    async def transcribe_async(
        self,
        audio_path: str,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        """
        Async wrapper for transcription.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.transcribe(audio_path, language),
        )
