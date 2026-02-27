"""Tests for Video Audio module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
import sys

# Mock the optional dependencies before importing
sys.modules['moviepy'] = MagicMock()
sys.modules['moviepy.editor'] = MagicMock()
sys.modules['speech_recognition'] = MagicMock()

from opencode.core.video.audio import (
    TranscriptionSegment,
    TranscriptionResult,
    AudioExtractor,
    AudioTranscriber,
    MOVIEPY_AVAILABLE,
    SPEECH_RECOGNITION_AVAILABLE,
)


class TestTranscriptionSegment:
    """Tests for TranscriptionSegment."""
    
    def test_default_values(self):
        """Test default values."""
        segment = TranscriptionSegment(text="Hello world")
        assert segment.text == "Hello world"
        assert segment.start_time == 0.0
        assert segment.end_time == 0.0
        assert segment.confidence == 0.0
    
    def test_custom_values(self):
        """Test custom values."""
        segment = TranscriptionSegment(
            text="Hello world",
            start_time=1.5,
            end_time=3.0,
            confidence=0.95
        )
        assert segment.text == "Hello world"
        assert segment.start_time == 1.5
        assert segment.end_time == 3.0
        assert segment.confidence == 0.95
    
    def test_to_dict(self):
        """Test to_dict method."""
        segment = TranscriptionSegment(
            text="Hello world",
            start_time=1.5,
            end_time=3.0,
            confidence=0.95
        )
        result = segment.to_dict()
        
        assert result["text"] == "Hello world"
        assert result["start_time"] == 1.5
        assert result["end_time"] == 3.0
        assert result["confidence"] == 0.95


class TestTranscriptionResult:
    """Tests for TranscriptionResult."""
    
    def test_default_values(self):
        """Test default values."""
        result = TranscriptionResult(text="Full text")
        assert result.text == "Full text"
        assert result.segments == []
        assert result.language == "en"
        assert result.duration == 0.0
        assert result.metadata == {}
    
    def test_custom_values(self):
        """Test custom values."""
        segment = TranscriptionSegment(text="Hello")
        result = TranscriptionResult(
            text="Full text",
            segments=[segment],
            language="es",
            duration=10.5,
            metadata={"engine": "whisper"}
        )
        assert result.text == "Full text"
        assert len(result.segments) == 1
        assert result.language == "es"
        assert result.duration == 10.5
    
    def test_to_dict(self):
        """Test to_dict method."""
        segment = TranscriptionSegment(text="Hello")
        result = TranscriptionResult(
            text="Full text",
            segments=[segment],
            language="es",
            duration=10.5,
            metadata={"engine": "whisper"}
        )
        d = result.to_dict()
        
        assert d["text"] == "Full text"
        assert len(d["segments"]) == 1
        assert d["language"] == "es"
        assert d["duration"] == 10.5
        assert d["metadata"]["engine"] == "whisper"


class TestAudioExtractor:
    """Tests for AudioExtractor."""
    
    def test_init_without_moviepy(self):
        """Test initialization fails without moviepy."""
        # Patch the module-level flag
        with patch('opencode.core.video.audio.MOVIEPY_AVAILABLE', False):
            with pytest.raises(ImportError) as exc_info:
                AudioExtractor()
            assert "moviepy" in str(exc_info.value).lower()
    
    def test_init_with_moviepy(self):
        """Test initialization with moviepy available."""
        with patch('opencode.core.video.audio.MOVIEPY_AVAILABLE', True):
            with patch('opencode.core.video.audio.VideoFileClip', MagicMock()):
                extractor = AudioExtractor()
                assert extractor.output_format == "wav"
                assert extractor.sample_rate == 16000
                assert extractor.channels == 1
    
    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        with patch('opencode.core.video.audio.MOVIEPY_AVAILABLE', True):
            with patch('opencode.core.video.audio.VideoFileClip', MagicMock()):
                extractor = AudioExtractor(
                    output_format="mp3",
                    sample_rate=44100,
                    channels=2
                )
                assert extractor.output_format == "mp3"
                assert extractor.sample_rate == 44100
                assert extractor.channels == 2
    
    def test_extract_audio_default_output(self):
        """Test extract_audio with default output path."""
        with patch('opencode.core.video.audio.MOVIEPY_AVAILABLE', True):
            mock_clip = MagicMock()
            mock_clip.duration = 10.0
            mock_clip.audio = MagicMock()
            mock_clip.__enter__ = MagicMock(return_value=mock_clip)
            mock_clip.__exit__ = MagicMock(return_value=False)
            
            with patch('opencode.core.video.audio.VideoFileClip', return_value=mock_clip):
                with patch('os.path.splitext', return_value=('test_video', '.mp4')):
                    with patch('os.path.basename', return_value='test_video.mp4'):
                        extractor = AudioExtractor()
                        result = extractor.extract_audio('test_video.mp4')
                        
                        assert result == 'test_video.wav'
    
    def test_extract_audio_custom_output(self):
        """Test extract_audio with custom output path."""
        with patch('opencode.core.video.audio.MOVIEPY_AVAILABLE', True):
            mock_clip = MagicMock()
            mock_clip.duration = 10.0
            mock_clip.audio = MagicMock()
            mock_clip.__enter__ = MagicMock(return_value=mock_clip)
            mock_clip.__exit__ = MagicMock(return_value=False)
            
            with patch('opencode.core.video.audio.VideoFileClip', return_value=mock_clip):
                extractor = AudioExtractor()
                result = extractor.extract_audio('video.mp4', output_path='custom.wav')
                
                assert result == 'custom.wav'
    
    def test_extract_audio_no_audio_track(self):
        """Test extract_audio fails when no audio track."""
        with patch('opencode.core.video.audio.MOVIEPY_AVAILABLE', True):
            mock_clip = MagicMock()
            mock_clip.duration = 10.0
            mock_clip.audio = None
            mock_clip.__enter__ = MagicMock(return_value=mock_clip)
            mock_clip.__exit__ = MagicMock(return_value=False)
            
            with patch('opencode.core.video.audio.VideoFileClip', return_value=mock_clip):
                extractor = AudioExtractor()
                
                with pytest.raises(ValueError) as exc_info:
                    extractor.extract_audio('video.mp4')
                assert "No audio track" in str(exc_info.value)
    
    def test_extract_audio_with_time_constraints(self):
        """Test extract_audio with start and end time."""
        with patch('opencode.core.video.audio.MOVIEPY_AVAILABLE', True):
            mock_clip = MagicMock()
            mock_clip.duration = 30.0
            mock_clip.audio = MagicMock()
            mock_clip.subclip = MagicMock(return_value=mock_clip)
            mock_clip.__enter__ = MagicMock(return_value=mock_clip)
            mock_clip.__exit__ = MagicMock(return_value=False)
            
            with patch('opencode.core.video.audio.VideoFileClip', return_value=mock_clip):
                extractor = AudioExtractor()
                result = extractor.extract_audio(
                    'video.mp4',
                    output_path='output.wav',
                    start_time=5.0,
                    end_time=15.0
                )
                
                mock_clip.subclip.assert_called_once_with(5.0, 15.0)
                assert result == 'output.wav'
    
    @pytest.mark.asyncio
    async def test_extract_audio_async(self):
        """Test async audio extraction."""
        with patch('opencode.core.video.audio.MOVIEPY_AVAILABLE', True):
            mock_clip = MagicMock()
            mock_clip.duration = 10.0
            mock_clip.audio = MagicMock()
            mock_clip.__enter__ = MagicMock(return_value=mock_clip)
            mock_clip.__exit__ = MagicMock(return_value=False)
            
            with patch('opencode.core.video.audio.VideoFileClip', return_value=mock_clip):
                extractor = AudioExtractor()
                
                # Mock the executor
                with patch('asyncio.get_event_loop') as mock_loop:
                    mock_loop.return_value.run_in_executor = AsyncMock(
                        return_value='output.wav'
                    )
                    result = await extractor.extract_audio_async('video.mp4', 'output.wav')
                    
                    assert result == 'output.wav'


class TestAudioTranscriber:
    """Tests for AudioTranscriber."""
    
    def test_init_without_speech_recognition(self):
        """Test initialization fails without SpeechRecognition."""
        with patch('opencode.core.video.audio.SPEECH_RECOGNITION_AVAILABLE', False):
            with pytest.raises(ImportError) as exc_info:
                AudioTranscriber()
            assert "SpeechRecognition" in str(exc_info.value)
    
    def test_init_with_speech_recognition(self):
        """Test initialization with SpeechRecognition available."""
        mock_sr = MagicMock()
        mock_sr.Recognizer = MagicMock(return_value=MagicMock())
        
        with patch('opencode.core.video.audio.SPEECH_RECOGNITION_AVAILABLE', True):
            with patch('opencode.core.video.audio.sr', mock_sr):
                transcriber = AudioTranscriber()
                assert transcriber.engine == "whisper"
                assert transcriber.language == "en-US"
                assert transcriber.model == "base"
    
    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        mock_sr = MagicMock()
        mock_sr.Recognizer = MagicMock(return_value=MagicMock())
        
        with patch('opencode.core.video.audio.SPEECH_RECOGNITION_AVAILABLE', True):
            with patch('opencode.core.video.audio.sr', mock_sr):
                transcriber = AudioTranscriber(
                    engine="google",
                    language="es-ES",
                    model="large"
                )
                assert transcriber.engine == "google"
                assert transcriber.language == "es-ES"
                assert transcriber.model == "large"
    
    def test_transcribe_unknown_engine(self):
        """Test transcribe with unknown engine."""
        mock_sr = MagicMock()
        mock_recognizer = MagicMock()
        mock_sr.Recognizer = MagicMock(return_value=mock_recognizer)
        
        with patch('opencode.core.video.audio.SPEECH_RECOGNITION_AVAILABLE', True):
            with patch('opencode.core.video.audio.sr', mock_sr):
                transcriber = AudioTranscriber(engine="unknown")
                
                # Mock AudioFile context manager
                mock_audio_file = MagicMock()
                mock_audio_file.__enter__ = MagicMock(return_value=mock_audio_file)
                mock_audio_file.__exit__ = MagicMock(return_value=False)
                
                with patch.object(mock_sr, 'AudioFile', return_value=mock_audio_file):
                    mock_recognizer.record = MagicMock(return_value=MagicMock())
                    
                    with pytest.raises(ValueError) as exc_info:
                        transcriber.transcribe('audio.wav')
                    assert "Unknown engine" in str(exc_info.value)
    
    def test_transcribe_whisper(self):
        """Test transcribe with Whisper engine."""
        mock_sr = MagicMock()
        mock_recognizer = MagicMock()
        mock_sr.Recognizer = MagicMock(return_value=mock_recognizer)
        mock_sr.UnknownValueError = Exception
        mock_sr.RequestError = Exception
        
        with patch('opencode.core.video.audio.SPEECH_RECOGNITION_AVAILABLE', True):
            with patch('opencode.core.video.audio.sr', mock_sr):
                transcriber = AudioTranscriber(engine="whisper")
                
                # Mock AudioFile context manager
                mock_audio_file = MagicMock()
                mock_audio_file.__enter__ = MagicMock(return_value=mock_audio_file)
                mock_audio_file.__exit__ = MagicMock(return_value=False)
                
                mock_audio_data = MagicMock()
                mock_recognizer.record = MagicMock(return_value=mock_audio_data)
                mock_recognizer.recognize_whisper = MagicMock(return_value="Hello world")
                
                with patch.object(mock_sr, 'AudioFile', return_value=mock_audio_file):
                    result = transcriber.transcribe('audio.wav')
                    
                    assert result.text == "Hello world"
                    assert result.metadata["engine"] == "whisper"
    
    def test_transcribe_google(self):
        """Test transcribe with Google engine."""
        mock_sr = MagicMock()
        mock_recognizer = MagicMock()
        mock_sr.Recognizer = MagicMock(return_value=mock_recognizer)
        mock_sr.UnknownValueError = Exception
        mock_sr.RequestError = Exception
        
        with patch('opencode.core.video.audio.SPEECH_RECOGNITION_AVAILABLE', True):
            with patch('opencode.core.video.audio.sr', mock_sr):
                transcriber = AudioTranscriber(engine="google")
                
                # Mock AudioFile context manager
                mock_audio_file = MagicMock()
                mock_audio_file.__enter__ = MagicMock(return_value=mock_audio_file)
                mock_audio_file.__exit__ = MagicMock(return_value=False)
                
                mock_audio_data = MagicMock()
                mock_recognizer.record = MagicMock(return_value=mock_audio_data)
                mock_recognizer.recognize_google = MagicMock(return_value="Hello from Google")
                
                with patch.object(mock_sr, 'AudioFile', return_value=mock_audio_file):
                    result = transcriber.transcribe('audio.wav')
                    
                    assert result.text == "Hello from Google"
                    assert result.metadata["engine"] == "google"
    
    def test_transcribe_sphinx(self):
        """Test transcribe with Sphinx engine."""
        mock_sr = MagicMock()
        mock_recognizer = MagicMock()
        mock_sr.Recognizer = MagicMock(return_value=mock_recognizer)
        mock_sr.UnknownValueError = Exception
        mock_sr.RequestError = Exception
        
        with patch('opencode.core.video.audio.SPEECH_RECOGNITION_AVAILABLE', True):
            with patch('opencode.core.video.audio.sr', mock_sr):
                transcriber = AudioTranscriber(engine="sphinx")
                
                # Mock AudioFile context manager
                mock_audio_file = MagicMock()
                mock_audio_file.__enter__ = MagicMock(return_value=mock_audio_file)
                mock_audio_file.__exit__ = MagicMock(return_value=False)
                
                mock_audio_data = MagicMock()
                mock_recognizer.record = MagicMock(return_value=mock_audio_data)
                mock_recognizer.recognize_sphinx = MagicMock(return_value="Hello from Sphinx")
                
                with patch.object(mock_sr, 'AudioFile', return_value=mock_audio_file):
                    result = transcriber.transcribe('audio.wav')
                    
                    assert result.text == "Hello from Sphinx"
                    assert result.metadata["engine"] == "sphinx"
    
    @pytest.mark.asyncio
    async def test_transcribe_async(self):
        """Test async transcription."""
        mock_sr = MagicMock()
        mock_recognizer = MagicMock()
        mock_sr.Recognizer = MagicMock(return_value=mock_recognizer)
        
        with patch('opencode.core.video.audio.SPEECH_RECOGNITION_AVAILABLE', True):
            with patch('opencode.core.video.audio.sr', mock_sr):
                transcriber = AudioTranscriber()
                
                with patch('asyncio.get_event_loop') as mock_loop:
                    mock_result = TranscriptionResult(text="Async result")
                    mock_loop.return_value.run_in_executor = AsyncMock(
                        return_value=mock_result
                    )
                    result = await transcriber.transcribe_async('audio.wav')
                    
                    assert result.text == "Async result"
    
    def test_transcribe_with_timestamps_fallback(self):
        """Test transcribe_with_timestamps falls back without whisper package."""
        mock_sr = MagicMock()
        mock_recognizer = MagicMock()
        mock_sr.Recognizer = MagicMock(return_value=mock_recognizer)
        mock_sr.UnknownValueError = Exception
        mock_sr.RequestError = Exception
        
        with patch('opencode.core.video.audio.SPEECH_RECOGNITION_AVAILABLE', True):
            with patch('opencode.core.video.audio.sr', mock_sr):
                transcriber = AudioTranscriber()
                
                # Mock the regular transcribe method
                transcriber.transcribe = MagicMock(
                    return_value=TranscriptionResult(text="Fallback result")
                )
                
                # Mock whisper import to fail
                with patch.dict(sys.modules, {'whisper': None}):
                    result = transcriber.transcribe_with_timestamps('audio.wav')
                    
                    assert result.text == "Fallback result"