"""Tests for Video Frames module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys

# Mock the optional dependencies before importing
sys.modules['moviepy'] = MagicMock()
sys.modules['moviepy.editor'] = MagicMock()

from opencode.core.video.frames import (
    ExtractedFrame,
    FrameExtractor,
    MOVIEPY_AVAILABLE,
)


class TestExtractedFrame:
    """Tests for ExtractedFrame."""
    
    def test_default_values(self):
        """Test default values."""
        frame = ExtractedFrame(
            frame_path="/path/to/frame.png",
            timestamp=1.5,
            frame_number=1
        )
        assert frame.frame_path == "/path/to/frame.png"
        assert frame.timestamp == 1.5
        assert frame.frame_number == 1
        assert frame.width == 0
        assert frame.height == 0
        assert frame.metadata == {}
    
    def test_custom_values(self):
        """Test custom values."""
        frame = ExtractedFrame(
            frame_path="/path/to/frame.png",
            timestamp=65.5,
            frame_number=10,
            width=1920,
            height=1080,
            metadata={"video": "test.mp4"}
        )
        assert frame.frame_path == "/path/to/frame.png"
        assert frame.timestamp == 65.5
        assert frame.frame_number == 10
        assert frame.width == 1920
        assert frame.height == 1080
    
    def test_timestamp_str_under_minute(self):
        """Test timestamp_str for under a minute."""
        frame = ExtractedFrame(
            frame_path="/path/to/frame.png",
            timestamp=45.0,
            frame_number=1
        )
        assert frame.timestamp_str == "00:45"
    
    def test_timestamp_str_over_minute(self):
        """Test timestamp_str for over a minute."""
        frame = ExtractedFrame(
            frame_path="/path/to/frame.png",
            timestamp=125.0,
            frame_number=1
        )
        assert frame.timestamp_str == "02:05"
    
    def test_to_dict(self):
        """Test to_dict method."""
        frame = ExtractedFrame(
            frame_path="/path/to/frame.png",
            timestamp=65.0,
            frame_number=10,
            width=1920,
            height=1080,
            metadata={"key": "value"}
        )
        d = frame.to_dict()
        
        assert d["frame_path"] == "/path/to/frame.png"
        assert d["timestamp"] == 65.0
        assert d["frame_number"] == 10
        assert d["width"] == 1920
        assert d["height"] == 1080
        assert d["timestamp_str"] == "01:05"
        assert d["metadata"]["key"] == "value"


class TestFrameExtractor:
    """Tests for FrameExtractor."""
    
    def test_init_without_moviepy(self):
        """Test initialization fails without moviepy."""
        with patch('opencode.core.video.frames.MOVIEPY_AVAILABLE', False):
            with pytest.raises(ImportError) as exc_info:
                FrameExtractor()
            assert "moviepy" in str(exc_info.value).lower()
    
    def test_init_with_moviepy(self):
        """Test initialization with moviepy available."""
        with patch('opencode.core.video.frames.MOVIEPY_AVAILABLE', True):
            with patch('opencode.core.video.frames.VideoFileClip', MagicMock()):
                extractor = FrameExtractor()
                assert extractor.fps == 0.5
                assert extractor.output_format == "png"
                assert extractor.output_dir == "./frames"
                assert extractor.naming_pattern == "frame_%04d"
    
    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        with patch('opencode.core.video.frames.MOVIEPY_AVAILABLE', True):
            with patch('opencode.core.video.frames.VideoFileClip', MagicMock()):
                extractor = FrameExtractor(
                    fps=1.0,
                    output_format="jpg",
                    output_dir="/custom/dir",
                    naming_pattern="img_%d"
                )
                assert extractor.fps == 1.0
                assert extractor.output_format == "jpg"
                assert extractor.output_dir == "/custom/dir"
                assert extractor.naming_pattern == "img_%d"
    
    def test_extract_frames(self):
        """Test extract_frames method."""
        with patch('opencode.core.video.frames.MOVIEPY_AVAILABLE', True):
            mock_clip = MagicMock()
            mock_clip.duration = 5.0
            mock_clip.w = 1920
            mock_clip.h = 1080
            mock_clip.__enter__ = MagicMock(return_value=mock_clip)
            mock_clip.__exit__ = MagicMock(return_value=False)
            
            with patch('opencode.core.video.frames.VideoFileClip', return_value=mock_clip):
                with patch('os.makedirs'):
                    extractor = FrameExtractor(fps=1.0)
                    frames = extractor.extract_frames('video.mp4')
                    
                    # With 5 second video at 1 fps, should get 5 frames
                    assert len(frames) == 5
                    assert frames[0].timestamp == 0.0
                    assert frames[0].frame_number == 1
    
    def test_extract_frames_with_time_constraints(self):
        """Test extract_frames with start and end time."""
        with patch('opencode.core.video.frames.MOVIEPY_AVAILABLE', True):
            mock_clip = MagicMock()
            mock_clip.duration = 10.0
            mock_clip.w = 1920
            mock_clip.h = 1080
            mock_clip.subclip = MagicMock(return_value=mock_clip)
            mock_clip.__enter__ = MagicMock(return_value=mock_clip)
            mock_clip.__exit__ = MagicMock(return_value=False)
            
            with patch('opencode.core.video.frames.VideoFileClip', return_value=mock_clip):
                with patch('os.makedirs'):
                    extractor = FrameExtractor(fps=1.0)
                    frames = extractor.extract_frames(
                        'video.mp4',
                        start_time=2.0,
                        end_time=5.0
                    )
                    
                    mock_clip.subclip.assert_called_once_with(2.0, 5.0)
    
    def test_extract_frames_custom_output_dir(self):
        """Test extract_frames with custom output directory."""
        with patch('opencode.core.video.frames.MOVIEPY_AVAILABLE', True):
            mock_clip = MagicMock()
            mock_clip.duration = 2.0
            mock_clip.w = 1920
            mock_clip.h = 1080
            mock_clip.__enter__ = MagicMock(return_value=mock_clip)
            mock_clip.__exit__ = MagicMock(return_value=False)
            
            with patch('opencode.core.video.frames.VideoFileClip', return_value=mock_clip):
                with patch('os.makedirs') as mock_makedirs:
                    extractor = FrameExtractor()
                    frames = extractor.extract_frames('video.mp4', output_dir='/custom/dir')
                    
                    mock_makedirs.assert_called_with('/custom/dir', exist_ok=True)
    
    def test_extract_key_frames(self):
        """Test extract_key_frames method."""
        with patch('opencode.core.video.frames.MOVIEPY_AVAILABLE', True):
            mock_clip = MagicMock()
            mock_clip.duration = 2.0
            mock_clip.w = 1920
            mock_clip.h = 1080
            mock_clip.__enter__ = MagicMock(return_value=mock_clip)
            mock_clip.__exit__ = MagicMock(return_value=False)
            
            with patch('opencode.core.video.frames.VideoFileClip', return_value=mock_clip):
                with patch('os.makedirs'):
                    extractor = FrameExtractor()
                    frames = extractor.extract_key_frames('video.mp4', threshold=0.5)
                    
                    # Currently just calls extract_frames
                    assert len(frames) > 0
    
    def test_extract_frames_at_timestamps(self):
        """Test extract_frames_at_timestamps method."""
        with patch('opencode.core.video.frames.MOVIEPY_AVAILABLE', True):
            mock_clip = MagicMock()
            mock_clip.duration = 10.0
            mock_clip.w = 1920
            mock_clip.h = 1080
            mock_clip.__enter__ = MagicMock(return_value=mock_clip)
            mock_clip.__exit__ = MagicMock(return_value=False)
            
            with patch('opencode.core.video.frames.VideoFileClip', return_value=mock_clip):
                with patch('os.makedirs'):
                    extractor = FrameExtractor()
                    frames = extractor.extract_frames_at_timestamps(
                        'video.mp4',
                        timestamps=[1.0, 3.0, 5.0]
                    )
                    
                    assert len(frames) == 3
                    assert frames[0].timestamp == 1.0
                    assert frames[1].timestamp == 3.0
                    assert frames[2].timestamp == 5.0
    
    def test_extract_frames_at_timestamps_out_of_range(self):
        """Test extract_frames_at_timestamps skips out of range timestamps."""
        with patch('opencode.core.video.frames.MOVIEPY_AVAILABLE', True):
            mock_clip = MagicMock()
            mock_clip.duration = 10.0
            mock_clip.w = 1920
            mock_clip.h = 1080
            mock_clip.__enter__ = MagicMock(return_value=mock_clip)
            mock_clip.__exit__ = MagicMock(return_value=False)
            
            with patch('opencode.core.video.frames.VideoFileClip', return_value=mock_clip):
                with patch('os.makedirs'):
                    extractor = FrameExtractor()
                    frames = extractor.extract_frames_at_timestamps(
                        'video.mp4',
                        timestamps=[-1.0, 5.0, 15.0]  # -1 and 15 are out of range
                    )
                    
                    # Only 5.0 should be extracted
                    assert len(frames) == 1
                    assert frames[0].timestamp == 5.0
    
    @pytest.mark.asyncio
    async def test_extract_frames_async(self):
        """Test async frame extraction."""
        with patch('opencode.core.video.frames.MOVIEPY_AVAILABLE', True):
            with patch('opencode.core.video.frames.VideoFileClip', MagicMock()):
                extractor = FrameExtractor()
                
                with patch('asyncio.get_event_loop') as mock_loop:
                    mock_frames = [
                        ExtractedFrame(
                            frame_path="frame.png",
                            timestamp=0.0,
                            frame_number=1
                        )
                    ]
                    mock_loop.return_value.run_in_executor = AsyncMock(
                        return_value=mock_frames
                    )
                    result = await extractor.extract_frames_async('video.mp4')
                    
                    assert len(result) == 1
    
    def test_get_video_info(self):
        """Test get_video_info static method."""
        mock_clip = MagicMock()
        mock_clip.duration = 120.0
        mock_clip.fps = 30.0
        mock_clip.w = 1920
        mock_clip.h = 1080
        mock_clip.size = (1920, 1080)
        mock_clip.audio = MagicMock()
        mock_clip.__enter__ = MagicMock(return_value=mock_clip)
        mock_clip.__exit__ = MagicMock(return_value=False)
        
        with patch('opencode.core.video.frames.MOVIEPY_AVAILABLE', True):
            with patch('opencode.core.video.frames.VideoFileClip', return_value=mock_clip):
                info = FrameExtractor.get_video_info('video.mp4')
                
                assert info["duration"] == 120.0
                assert info["fps"] == 30.0
                assert info["width"] == 1920
                assert info["height"] == 1080
                assert info["has_audio"] is True
    
    def test_get_video_info_no_audio(self):
        """Test get_video_info with no audio track."""
        mock_clip = MagicMock()
        mock_clip.duration = 120.0
        mock_clip.fps = 30.0
        mock_clip.w = 1920
        mock_clip.h = 1080
        mock_clip.size = (1920, 1080)
        mock_clip.audio = None
        mock_clip.__enter__ = MagicMock(return_value=mock_clip)
        mock_clip.__exit__ = MagicMock(return_value=False)
        
        with patch('opencode.core.video.frames.MOVIEPY_AVAILABLE', True):
            with patch('opencode.core.video.frames.VideoFileClip', return_value=mock_clip):
                info = FrameExtractor.get_video_info('video.mp4')
                
                assert info["has_audio"] is False
    
    def test_get_video_info_without_moviepy(self):
        """Test get_video_info fails without moviepy."""
        with patch('opencode.core.video.frames.MOVIEPY_AVAILABLE', False):
            with pytest.raises(ImportError) as exc_info:
                FrameExtractor.get_video_info('video.mp4')
            assert "moviepy" in str(exc_info.value).lower()