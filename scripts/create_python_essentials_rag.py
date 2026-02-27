#!/usr/bin/env python3
"""
Create a RAG from the Python Essentials for AI Agents YouTube video.

This script:
1. Fetches the transcript from the YouTube video
2. Creates text files from the transcript
3. Creates a RAG index for agents to use

Video: Python Essentials for AI Agents
URL: https://youtu.be/UsfpzxZNsPo?si=cc0kTt-AVOhKDxq5
"""

import asyncio
import json
import sys
from pathlib import Path


async def fetch_transcript(video_url: str) -> list:
    """Fetch transcript from YouTube video."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        print("ERROR: youtube-transcript-api not installed")
        print("Install with: pip install youtube-transcript-api")
        sys.exit(1)
    
    # Extract video ID
    video_id = None
    if "youtu.be/" in video_url:
        video_id = video_url.split("youtu.be/")[1].split("?")[0]
    elif "watch?v=" in video_url:
        video_id = video_url.split("watch?v=")[1].split("&")[0]
    
    if not video_id:
        print("ERROR: Could not extract video ID from URL")
        sys.exit(1)
    
    print(f"Fetching transcript for video: {video_id}")
    
    api = YouTubeTranscriptApi()
    try:
        transcript = api.fetch(video_id)
        return list(transcript)
    except Exception as e:
        print(f"ERROR fetching transcript: {e}")
        sys.exit(1)


def create_transcript_files(transcript: list, output_dir: Path, video_id: str):
    """Create text files from transcript."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Group transcript into chunks
    chunk_size = 50  # lines per file
    chunks = []
    current_chunk = []
    
    for entry in transcript:
        # Handle both dict-like and object access
        if hasattr(entry, 'text'):
            text = entry.text
            start = entry.start
        else:
            text = entry.get("text", "")
            start = entry.get("start", 0)
        
        current_chunk.append({"text": text, "start": start})
        
        if len(current_chunk) >= chunk_size:
            chunks.append(current_chunk)
            current_chunk = []
    
    # Don't forget the last chunk
    if current_chunk:
        chunks.append(current_chunk)
    
    print(f"Creating {len(chunks)} transcript files...")
    
    for i, chunk in enumerate(chunks):
        filename = output_dir / f"transcript_part_{i+1:03d}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# Python Essentials for AI Agents - Part {i+1}\n")
            f.write(f"# Video ID: {video_id}\n\n")
            
            for entry in chunk:
                timestamp = int(entry.get("start", 0))
                minutes = timestamp // 60
                seconds = timestamp % 60
                text = entry.get("text", "")
                f.write(f"[{minutes:02d}:{seconds:02d}] {text}\n")
        
        print(f"  Created: {filename.name}")
    
    return len(chunks)


async def create_rag(sources: list, agent_name: str = "python_essentials"):
    """Create a RAG from the sources."""
    from opencode.core.rag.agent_rag_manager import AgentRAGManager
    
    print(f"\nCreating RAG for agent: {agent_name}")
    
    manager = AgentRAGManager()
    
    try:
        config = await manager.create_rag(
            agent=agent_name,
            sources=sources,
            description="Python Essentials for AI Agents - YouTube video transcript",
        )
        print(f"RAG created successfully!")
        print(f"  Agent: {agent_name}")
        print(f"  Documents: {config.document_count}")
        return config
    except Exception as e:
        print(f"ERROR creating RAG: {e}")
        # Try alternative approach
        print("\nTrying alternative RAG creation...")
        return None


def create_rag_via_cli(sources: list, agent_name: str = "python_essentials"):
    """Create RAG using CLI approach."""
    import subprocess
    
    sources_arg = " ".join([f"-s {s}" for s in sources])
    cmd = f"python -m opencode.cli.main rag create {agent_name} {sources_arg}"
    
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    return result.returncode == 0


def main():
    """Main entry point."""
    video_url = "https://youtu.be/UsfpzxZNsPo?si=cc0kTt-AVOhKDxq5"
    video_id = "UsfpzxZNsPo"
    
    print("=" * 60)
    print("Python Essentials for AI Agents - RAG Creator")
    print("=" * 60)
    print(f"Video URL: {video_url}")
    print()
    
    # Step 1: Fetch transcript
    print("Step 1: Fetching transcript...")
    transcript = asyncio.run(fetch_transcript(video_url))
    print(f"  Got {len(transcript)} transcript entries")
    
    # Step 2: Create transcript files
    print("\nStep 2: Creating transcript files...")
    output_dir = Path("RAG/agent_python_essentials/transcript")
    num_files = create_transcript_files(transcript, output_dir, video_id)
    print(f"  Created {num_files} transcript files")
    
    # Step 3: Create RAG
    print("\nStep 3: Creating RAG...")
    sources = [str(output_dir)]
    
    # Try AgentRAGManager first
    config = asyncio.run(create_rag(sources))
    
    if config is None:
        # Fall back to CLI
        print("Using CLI approach...")
        create_rag_via_cli(sources)
    
    print("\n" + "=" * 60)
    print("RAG creation complete!")
    print("=" * 60)
    print(f"\nRAG location: RAG/agent_python_essentials")
    print(f"Transcript files: {output_dir}")
    print(f"\nTo query the RAG:")
    print(f"  python -m opencode.cli.main rag query python_essentials '<question>'")


if __name__ == "__main__":
    main()
