"""
Transcript Chunking Strategies

Provides various chunking strategies for YouTube transcripts to optimize
RAG retrieval while preserving context and timing information.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

from .transcript import TranscriptChunk, VideoTranscript


class ChunkingStrategy(str, Enum):
    """Available chunking strategies"""
    FIXED_SIZE = "fixed_size"  # Fixed number of chunks per group
    TIME_BASED = "time_based"  # Based on time duration
    SENTENCE = "sentence"      # Based on sentence boundaries
    SEMANTIC = "semantic"      # Based on semantic similarity (requires embeddings)


class ChunkingConfig(BaseModel):
    """Configuration for transcript chunking"""
    strategy: ChunkingStrategy = Field(
        default=ChunkingStrategy.FIXED_SIZE,
        description="Chunking strategy to use"
    )
    chunk_size: int = Field(
        default=10,
        description="Number of original chunks to combine (for fixed_size)"
    )
    target_duration: float = Field(
        default=30.0,
        description="Target duration in seconds (for time_based)"
    )
    overlap: int = Field(
        default=0,
        description="Number of chunks to overlap"
    )
    min_chunk_size: int = Field(
        default=1,
        description="Minimum chunks per group"
    )
    max_chunk_size: int = Field(
        default=20,
        description="Maximum chunks per group"
    )


class ChunkedTranscript(BaseModel):
    """A chunked transcript segment for RAG indexing"""
    text: str = Field(..., description="Combined text content")
    start: float = Field(..., description="Start time in seconds")
    duration: float = Field(..., description="Total duration in seconds")
    end: float = Field(..., description="End time in seconds")
    video_id: str = Field(..., description="Source video ID")
    chunk_index: int = Field(..., description="Index of this chunk")
    original_chunks: int = Field(..., description="Number of original chunks combined")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "text": self.text,
            "start": self.start,
            "duration": self.duration,
            "end": self.end,
            "video_id": self.video_id,
            "chunk_index": self.chunk_index,
            "original_chunks": self.original_chunks,
            "metadata": self.metadata,
        }


class TranscriptChunker:
    """
    Chunk transcripts using various strategies.
    
    The chunker combines small transcript segments into larger chunks
    that are more suitable for RAG retrieval while preserving timing
    information for timestamped results.
    """
    
    def __init__(self, config: Optional[ChunkingConfig] = None):
        """
        Initialize the chunker.
        
        Args:
            config: Chunking configuration
        """
        self.config = config or ChunkingConfig()
    
    def chunk(self, transcript: VideoTranscript) -> List[ChunkedTranscript]:
        """
        Chunk a transcript using the configured strategy.
        
        Args:
            transcript: Video transcript to chunk
            
        Returns:
            List of chunked transcript segments
        """
        if not transcript.chunks:
            return []
        
        strategy = self.config.strategy
        
        if strategy == ChunkingStrategy.FIXED_SIZE:
            return self._chunk_fixed_size(transcript)
        elif strategy == ChunkingStrategy.TIME_BASED:
            return self._chunk_time_based(transcript)
        elif strategy == ChunkingStrategy.SENTENCE:
            return self._chunk_sentence(transcript)
        elif strategy == ChunkingStrategy.SEMANTIC:
            # Semantic chunking requires embeddings - fall back to sentence
            return self._chunk_sentence(transcript)
        else:
            return self._chunk_fixed_size(transcript)
    
    def _chunk_fixed_size(self, transcript: VideoTranscript) -> List[ChunkedTranscript]:
        """Chunk by fixed number of original chunks"""
        chunks = transcript.chunks
        chunk_size = self.config.chunk_size
        overlap = self.config.overlap
        
        result = []
        i = 0
        chunk_index = 0
        
        while i < len(chunks):
            # Get chunk range
            end_idx = min(i + chunk_size, len(chunks))
            chunk_group = chunks[i:end_idx]
            
            # Combine text
            combined_text = " ".join(c.text for c in chunk_group)
            
            # Calculate timing
            start_time = chunk_group[0].start
            duration = sum(c.duration for c in chunk_group)
            
            result.append(ChunkedTranscript(
                text=combined_text,
                start=start_time,
                duration=duration,
                end=start_time + duration,
                video_id=transcript.video_id,
                chunk_index=chunk_index,
                original_chunks=len(chunk_group),
                metadata={
                    "language": transcript.language,
                    "strategy": "fixed_size",
                }
            ))
            
            chunk_index += 1
            i += chunk_size - overlap
        
        return result
    
    def _chunk_time_based(self, transcript: VideoTranscript) -> List[ChunkedTranscript]:
        """Chunk by target duration"""
        chunks = transcript.chunks
        target_duration = self.config.target_duration
        
        result = []
        current_group = []
        current_duration = 0.0
        chunk_index = 0
        
        for chunk in chunks:
            current_group.append(chunk)
            current_duration += chunk.duration
            
            if current_duration >= target_duration:
                # Create chunked segment
                combined_text = " ".join(c.text for c in current_group)
                start_time = current_group[0].start
                
                result.append(ChunkedTranscript(
                    text=combined_text,
                    start=start_time,
                    duration=current_duration,
                    end=start_time + current_duration,
                    video_id=transcript.video_id,
                    chunk_index=chunk_index,
                    original_chunks=len(current_group),
                    metadata={
                        "language": transcript.language,
                        "strategy": "time_based",
                    }
                ))
                
                chunk_index += 1
                current_group = []
                current_duration = 0.0
        
        # Handle remaining chunks
        if current_group:
            combined_text = " ".join(c.text for c in current_group)
            start_time = current_group[0].start
            
            result.append(ChunkedTranscript(
                text=combined_text,
                start=start_time,
                duration=current_duration,
                end=start_time + current_duration,
                video_id=transcript.video_id,
                chunk_index=chunk_index,
                original_chunks=len(current_group),
                metadata={
                    "language": transcript.language,
                    "strategy": "time_based",
                }
            ))
        
        return result
    
    def _chunk_sentence(self, transcript: VideoTranscript) -> List[ChunkedTranscript]:
        """Chunk by sentence boundaries"""
        chunks = transcript.chunks
        
        result = []
        current_group = []
        current_text = ""
        chunk_index = 0
        
        # Sentence-ending punctuation
        sentence_enders = {'.', '!', '?'}
        
        for chunk in chunks:
            current_group.append(chunk)
            current_text += " " + chunk.text if current_text else chunk.text
            
            # Check for sentence end
            stripped = chunk.text.strip()
            if stripped and stripped[-1] in sentence_enders:
                # Create chunked segment
                start_time = current_group[0].start
                duration = sum(c.duration for c in current_group)
                
                result.append(ChunkedTranscript(
                    text=current_text.strip(),
                    start=start_time,
                    duration=duration,
                    end=start_time + duration,
                    video_id=transcript.video_id,
                    chunk_index=chunk_index,
                    original_chunks=len(current_group),
                    metadata={
                        "language": transcript.language,
                        "strategy": "sentence",
                    }
                ))
                
                chunk_index += 1
                current_group = []
                current_text = ""
        
        # Handle remaining text
        if current_group:
            start_time = current_group[0].start
            duration = sum(c.duration for c in current_group)
            
            result.append(ChunkedTranscript(
                text=current_text.strip(),
                start=start_time,
                duration=duration,
                end=start_time + duration,
                video_id=transcript.video_id,
                chunk_index=chunk_index,
                original_chunks=len(current_group),
                metadata={
                    "language": transcript.language,
                    "strategy": "sentence",
                }
            ))
        
        return result
    
    def chunk_with_overlap(
        self,
        transcript: VideoTranscript,
        overlap_chunks: int = 2,
    ) -> List[ChunkedTranscript]:
        """
        Chunk with explicit overlap for better context preservation.
        
        Args:
            transcript: Video transcript
            overlap_chunks: Number of chunks to overlap between segments
            
        Returns:
            List of overlapping chunked segments
        """
        config = ChunkingConfig(
            strategy=ChunkingStrategy.FIXED_SIZE,
            chunk_size=self.config.chunk_size,
            overlap=overlap_chunks,
        )
        chunker = TranscriptChunker(config)
        return chunker.chunk(transcript)
