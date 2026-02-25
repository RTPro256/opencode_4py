"""Tests for Mention Processing module."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from opencode.core.context.mentions import (
    MentionType,
    Mention,
    ProcessedMentions,
    MentionProcessor,
)


class TestMentionType:
    """Tests for MentionType enum."""

    def test_mention_types(self):
        """Test all mention types exist."""
        assert MentionType.FILE.value == "file"
        assert MentionType.DIRECTORY.value == "directory"
        assert MentionType.PERSON.value == "person"
        assert MentionType.TOOL.value == "tool"
        assert MentionType.MODE.value == "mode"
        assert MentionType.SKILL.value == "skill"
        assert MentionType.VARIABLE.value == "variable"
        assert MentionType.URL.value == "url"


class TestMention:
    """Tests for Mention dataclass."""

    def test_mention_creation(self):
        """Test creating a mention."""
        mention = Mention(
            mention_type=MentionType.FILE,
            value="src/main.py",
            raw_text="@file:src/main.py",
            start_pos=0,
            end_pos=17,
        )
        
        assert mention.mention_type == MentionType.FILE
        assert mention.value == "src/main.py"
        assert mention.raw_text == "@file:src/main.py"
        assert mention.start_pos == 0
        assert mention.end_pos == 17
        assert mention.resolved is False
        assert mention.resolved_value is None

    def test_mention_with_metadata(self):
        """Test mention with metadata."""
        mention = Mention(
            mention_type=MentionType.FILE,
            value="test.py",
            raw_text="@file:test.py",
            start_pos=0,
            end_pos=12,
            metadata={"exists": True, "size": 1024},
        )
        
        assert mention.metadata["exists"] is True
        assert mention.metadata["size"] == 1024

    def test_mention_to_dict(self):
        """Test converting mention to dictionary."""
        mention = Mention(
            mention_type=MentionType.FILE,
            value="test.py",
            raw_text="@file:test.py",
            start_pos=0,
            end_pos=12,
            resolved=True,
            resolved_value="/path/to/test.py",
        )
        
        result = mention.to_dict()
        
        assert result["mention_type"] == "file"
        assert result["value"] == "test.py"
        assert result["raw_text"] == "@file:test.py"
        assert result["start_pos"] == 0
        assert result["end_pos"] == 12
        assert result["resolved"] is True
        assert result["resolved_value"] == "/path/to/test.py"


class TestProcessedMentions:
    """Tests for ProcessedMentions dataclass."""

    def test_processed_mentions_creation(self):
        """Test creating processed mentions."""
        mentions = [
            Mention(MentionType.FILE, "test.py", "@file:test.py", 0, 12),
            Mention(MentionType.DIRECTORY, "src", "@dir:src", 13, 20),
        ]
        
        processed = ProcessedMentions(
            original_text="@file:test.py @dir:src",
            processed_text="resolved text",
            mentions=mentions,
        )
        
        assert processed.original_text == "@file:test.py @dir:src"
        assert processed.processed_text == "resolved text"
        assert len(processed.mentions) == 2

    def test_file_mentions_property(self):
        """Test file_mentions property."""
        mentions = [
            Mention(MentionType.FILE, "test.py", "@file:test.py", 0, 12),
            Mention(MentionType.DIRECTORY, "src", "@dir:src", 13, 20),
            Mention(MentionType.FILE, "main.py", "@file:main.py", 21, 33),
        ]
        
        processed = ProcessedMentions(
            original_text="text",
            processed_text="text",
            mentions=mentions,
        )
        
        file_mentions = processed.file_mentions
        
        assert len(file_mentions) == 2
        assert all(m.mention_type == MentionType.FILE for m in file_mentions)

    def test_directory_mentions_property(self):
        """Test directory_mentions property."""
        mentions = [
            Mention(MentionType.FILE, "test.py", "@file:test.py", 0, 12),
            Mention(MentionType.DIRECTORY, "src", "@dir:src", 13, 20),
        ]
        
        processed = ProcessedMentions(
            original_text="text",
            processed_text="text",
            mentions=mentions,
        )
        
        dir_mentions = processed.directory_mentions
        
        assert len(dir_mentions) == 1
        assert dir_mentions[0].mention_type == MentionType.DIRECTORY

    def test_tool_mentions_property(self):
        """Test tool_mentions property."""
        mentions = [
            Mention(MentionType.TOOL, "bash", "@tool:bash", 0, 10),
            Mention(MentionType.FILE, "test.py", "@file:test.py", 11, 23),
        ]
        
        processed = ProcessedMentions(
            original_text="text",
            processed_text="text",
            mentions=mentions,
        )
        
        tool_mentions = processed.tool_mentions
        
        assert len(tool_mentions) == 1
        assert tool_mentions[0].value == "bash"

    def test_mode_mentions_property(self):
        """Test mode_mentions property."""
        mentions = [
            Mention(MentionType.MODE, "architect", "@mode:architect", 0, 15),
        ]
        
        processed = ProcessedMentions(
            original_text="text",
            processed_text="text",
            mentions=mentions,
        )
        
        mode_mentions = processed.mode_mentions
        
        assert len(mode_mentions) == 1
        assert mode_mentions[0].value == "architect"

    def test_skill_mentions_property(self):
        """Test skill_mentions property."""
        mentions = [
            Mention(MentionType.SKILL, "python", "@skill:python", 0, 13),
        ]
        
        processed = ProcessedMentions(
            original_text="text",
            processed_text="text",
            mentions=mentions,
        )
        
        skill_mentions = processed.skill_mentions
        
        assert len(skill_mentions) == 1
        assert skill_mentions[0].value == "python"


class TestMentionProcessor:
    """Tests for MentionProcessor class."""

    def test_init_default(self):
        """Test default initialization."""
        processor = MentionProcessor()
        
        assert processor.workspace_root is None
        assert processor.resolve_files is True
        assert processor.resolve_urls is True

    def test_init_custom(self):
        """Test custom initialization."""
        processor = MentionProcessor(
            workspace_root="/project",
            resolve_files=False,
            resolve_urls=False,
        )
        
        assert processor.workspace_root == Path("/project")
        assert processor.resolve_files is False
        assert processor.resolve_urls is False

    def test_process_no_mentions(self):
        """Test processing text with no mentions."""
        processor = MentionProcessor()
        
        result = processor.process("Hello world!")
        
        assert result.original_text == "Hello world!"
        assert result.processed_text == "Hello world!"
        assert len(result.mentions) == 0

    def test_process_file_mention(self):
        """Test processing file mention."""
        processor = MentionProcessor()
        
        result = processor.process("Read @file:src/main.py")
        
        assert len(result.mentions) == 1
        assert result.mentions[0].mention_type == MentionType.FILE
        assert result.mentions[0].value == "src/main.py"

    def test_process_directory_mention(self):
        """Test processing directory mention."""
        processor = MentionProcessor()
        
        result = processor.process("Check @dir:tests")
        
        assert len(result.mentions) == 1
        assert result.mentions[0].mention_type == MentionType.DIRECTORY
        assert result.mentions[0].value == "tests"

    def test_process_tool_mention(self):
        """Test processing tool mention."""
        processor = MentionProcessor()
        
        result = processor.process("Use @tool:bash to run")
        
        assert len(result.mentions) == 1
        assert result.mentions[0].mention_type == MentionType.TOOL
        assert result.mentions[0].value == "bash"

    def test_process_mode_mention(self):
        """Test processing mode mention."""
        processor = MentionProcessor()
        
        result = processor.process("Switch to @mode:architect")
        
        assert len(result.mentions) == 1
        assert result.mentions[0].mention_type == MentionType.MODE
        assert result.mentions[0].value == "architect"

    def test_process_skill_mention(self):
        """Test processing skill mention."""
        processor = MentionProcessor()
        
        result = processor.process("Use @skill:python")
        
        assert len(result.mentions) == 1
        assert result.mentions[0].mention_type == MentionType.SKILL
        assert result.mentions[0].value == "python"

    def test_process_person_mention(self):
        """Test processing person mention."""
        processor = MentionProcessor()
        
        result = processor.process("Ask @john for help")
        
        assert len(result.mentions) == 1
        assert result.mentions[0].mention_type == MentionType.PERSON
        assert result.mentions[0].value == "john"

    def test_process_url_mention(self):
        """Test processing URL mention."""
        processor = MentionProcessor()
        
        result = processor.process("Visit @url:https://example.com")
        
        assert len(result.mentions) == 1
        assert result.mentions[0].mention_type == MentionType.URL
        assert result.mentions[0].value == "https://example.com"

    def test_process_variable_mention(self):
        """Test processing variable mention."""
        processor = MentionProcessor()
        
        result = processor.process("Use @var:config")
        
        assert len(result.mentions) == 1
        assert result.mentions[0].mention_type == MentionType.VARIABLE
        assert result.mentions[0].value == "config"

    def test_process_multiple_mentions(self):
        """Test processing multiple mentions."""
        processor = MentionProcessor()
        
        result = processor.process("Read @file:main.py and @file:test.py")
        
        assert len(result.mentions) == 2
        assert result.mentions[0].value == "main.py"
        assert result.mentions[1].value == "test.py"

    def test_process_mixed_mentions(self):
        """Test processing mixed mention types."""
        processor = MentionProcessor()
        
        result = processor.process("Read @file:main.py with @tool:bash and @john")
        
        assert len(result.mentions) == 3
        types = [m.mention_type for m in result.mentions]
        assert MentionType.FILE in types
        assert MentionType.TOOL in types
        assert MentionType.PERSON in types

    def test_extract_files(self):
        """Test extract_files method."""
        processor = MentionProcessor()
        
        files = processor.extract_files("Read @file:main.py and @file:test.py")
        
        assert len(files) == 2
        assert "main.py" in files
        assert "test.py" in files

    def test_extract_directories(self):
        """Test extract_directories method."""
        processor = MentionProcessor()
        
        dirs = processor.extract_directories("Check @dir:src and @dir:tests")
        
        assert len(dirs) == 2
        assert "src" in dirs
        assert "tests" in dirs

    def test_replace_mentions_all(self):
        """Test replacing all mentions."""
        processor = MentionProcessor()
        
        result = processor.replace_mentions(
            "Read @file:main.py and @file:test.py",
            "[FILE]"
        )
        
        assert result == "Read [FILE] and [FILE]"

    def test_replace_mentions_by_type(self):
        """Test replacing mentions by type."""
        processor = MentionProcessor()
        
        result = processor.replace_mentions(
            "Read @file:main.py with @tool:bash",
            "[REPLACED]",
            mention_type=MentionType.FILE
        )
        
        assert "[REPLACED]" in result
        assert "@tool:bash" in result

    def test_get_mention_summary_no_mentions(self):
        """Test summary with no mentions."""
        processor = MentionProcessor()
        
        summary = processor.get_mention_summary("Hello world!")
        
        assert "No mentions found" in summary

    def test_get_mention_summary_with_mentions(self):
        """Test summary with mentions."""
        processor = MentionProcessor()
        
        summary = processor.get_mention_summary("Read @file:main.py and @tool:bash")
        
        assert "2 mentions" in summary
        assert "file:" in summary
        assert "tool:" in summary


class TestMentionProcessorWithWorkspace:
    """Tests for MentionProcessor with workspace root."""

    def test_resolve_file_mention_exists(self, tmp_path):
        """Test resolving file mention that exists."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")
        
        processor = MentionProcessor(workspace_root=str(tmp_path))
        
        result = processor.process("Read @file:test.py")
        
        assert len(result.mentions) == 1
        assert result.mentions[0].resolved is True
        assert result.mentions[0].metadata.get("exists") is True

    def test_resolve_file_mention_not_exists(self, tmp_path):
        """Test resolving file mention that doesn't exist."""
        processor = MentionProcessor(workspace_root=str(tmp_path))
        
        result = processor.process("Read @file:nonexistent.py")
        
        assert len(result.mentions) == 1
        assert result.mentions[0].resolved is False
        assert result.mentions[0].metadata.get("exists") is False

    def test_resolve_directory_mention_exists(self, tmp_path):
        """Test resolving directory mention that exists."""
        # Create a test directory
        test_dir = tmp_path / "src"
        test_dir.mkdir()
        
        processor = MentionProcessor(workspace_root=str(tmp_path))
        
        result = processor.process("Check @dir:src")
        
        assert len(result.mentions) == 1
        assert result.mentions[0].resolved is True
        assert result.mentions[0].metadata.get("exists") is True

    def test_resolve_directory_mention_not_exists(self, tmp_path):
        """Test resolving directory mention that doesn't exist."""
        processor = MentionProcessor(workspace_root=str(tmp_path))
        
        result = processor.process("Check @dir:nonexistent")
        
        assert len(result.mentions) == 1
        assert result.mentions[0].resolved is False
        assert result.mentions[0].metadata.get("exists") is False

    def test_resolve_files_disabled(self, tmp_path):
        """Test with file resolution disabled."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")
        
        processor = MentionProcessor(
            workspace_root=str(tmp_path),
            resolve_files=False
        )
        
        result = processor.process("Read @file:test.py")
        
        assert len(result.mentions) == 1
        # Should not be resolved when resolve_files is False
        assert result.mentions[0].resolved is False

    def test_resolve_url_mention(self):
        """Test resolving URL mention."""
        processor = MentionProcessor(resolve_urls=True)
        
        result = processor.process("Visit @url:https://example.com")
        
        assert len(result.mentions) == 1
        assert result.mentions[0].resolved is True

    def test_resolve_url_disabled(self):
        """Test with URL resolution disabled."""
        processor = MentionProcessor(resolve_urls=False)
        
        result = processor.process("Visit @url:https://example.com")
        
        assert len(result.mentions) == 1
        # Should not be resolved when resolve_urls is False
        assert result.mentions[0].resolved is False
