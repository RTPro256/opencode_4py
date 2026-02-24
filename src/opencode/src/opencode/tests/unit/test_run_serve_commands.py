"""
Tests for CLI run and serve commands.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio


class TestRunCommand:
    """Tests for the run command."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config."""
        config = MagicMock()
        config.data_dir = MagicMock()
        config.data_dir.__truediv__ = MagicMock(return_value=MagicMock())
        provider_config = MagicMock()
        provider_config.api_key = "test-api-key"
        config.get_provider_config = MagicMock(return_value=provider_config)
        return config

    @pytest.fixture
    def mock_provider(self):
        """Create a mock provider."""
        provider = MagicMock()
        provider.stream = AsyncMock()
        provider.complete = AsyncMock()
        return provider

    def test_run_command_imports(self):
        """Test that run command module can be imported."""
        from opencode.cli.commands.run import run_command, _run_async
        assert callable(run_command)
        assert callable(_run_async)

    @pytest.mark.asyncio
    async def test_run_async_anthropic_provider(self, mock_config, mock_provider):
        """Test _run_async with Anthropic provider."""
        from opencode.cli.commands.run import _run_async
        
        # Mock the response
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=5)
        mock_provider.complete.return_value = mock_response
        
        with patch("opencode.cli.commands.run.Config.load", return_value=mock_config), \
             patch("opencode.cli.commands.run.init_database", new_callable=AsyncMock), \
             patch("opencode.cli.commands.run.close_database", new_callable=AsyncMock), \
             patch("opencode.cli.commands.run.AnthropicProvider", return_value=mock_provider), \
             patch("opencode.cli.commands.run.console") as mock_console:
            
            await _run_async(
                prompt="Test prompt",
                model="claude-3-5-sonnet-20241022",
                provider_name="anthropic",
                project=MagicMock(),
                stream=False,
                system=None,
            )
            
            # Verify provider was created with correct params
            mock_provider.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_async_openai_provider(self, mock_config, mock_provider):
        """Test _run_async with OpenAI provider."""
        from opencode.cli.commands.run import _run_async
        
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=5)
        mock_provider.complete.return_value = mock_response
        
        with patch("opencode.cli.commands.run.Config.load", return_value=mock_config), \
             patch("opencode.cli.commands.run.init_database", new_callable=AsyncMock), \
             patch("opencode.cli.commands.run.close_database", new_callable=AsyncMock), \
             patch("opencode.cli.commands.run.OpenAIProvider", return_value=mock_provider), \
             patch("opencode.cli.commands.run.console") as mock_console:
            
            await _run_async(
                prompt="Test prompt",
                model="gpt-4o",
                provider_name="openai",
                project=MagicMock(),
                stream=False,
                system=None,
            )
            
            mock_provider.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_async_with_system_prompt(self, mock_config, mock_provider):
        """Test _run_async with system prompt."""
        from opencode.cli.commands.run import _run_async
        
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_response.usage = None
        mock_provider.complete.return_value = mock_response
        
        with patch("opencode.cli.commands.run.Config.load", return_value=mock_config), \
             patch("opencode.cli.commands.run.init_database", new_callable=AsyncMock), \
             patch("opencode.cli.commands.run.close_database", new_callable=AsyncMock), \
             patch("opencode.cli.commands.run.AnthropicProvider", return_value=mock_provider), \
             patch("opencode.cli.commands.run.console"):
            
            await _run_async(
                prompt="Test prompt",
                model="claude-3-5-sonnet-20241022",
                provider_name="anthropic",
                project=MagicMock(),
                stream=False,
                system="You are a helpful assistant",
            )
            
            # Verify messages include system prompt
            call_args = mock_provider.complete.call_args
            messages = call_args[0][0]
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert messages[0]["content"] == "You are a helpful assistant"

    @pytest.mark.asyncio
    async def test_run_async_streaming(self, mock_config, mock_provider):
        """Test _run_async with streaming enabled."""
        from opencode.cli.commands.run import _run_async
        
        # Create async generator for streaming
        async def mock_stream(messages, **kwargs):
            chunks = [
                MagicMock(content="Hello"),
                MagicMock(content=" world"),
                MagicMock(content="!"),
            ]
            for chunk in chunks:
                yield chunk
        
        mock_provider.stream = mock_stream
        
        with patch("opencode.cli.commands.run.Config.load", return_value=mock_config), \
             patch("opencode.cli.commands.run.init_database", new_callable=AsyncMock), \
             patch("opencode.cli.commands.run.close_database", new_callable=AsyncMock), \
             patch("opencode.cli.commands.run.AnthropicProvider", return_value=mock_provider), \
             patch("opencode.cli.commands.run.console"):
            
            await _run_async(
                prompt="Test prompt",
                model="claude-3-5-sonnet-20241022",
                provider_name="anthropic",
                project=MagicMock(),
                stream=True,
                system=None,
            )

    @pytest.mark.asyncio
    async def test_run_async_no_api_key(self, mock_config):
        """Test _run_async when no API key is configured."""
        from opencode.cli.commands.run import _run_async
        import typer
        
        # Mock config with no API key
        provider_config = MagicMock()
        provider_config.api_key = None
        mock_config.get_provider_config = MagicMock(return_value=provider_config)
        
        with patch("opencode.cli.commands.run.Config.load", return_value=mock_config), \
             patch("opencode.cli.commands.run.init_database", new_callable=AsyncMock), \
             patch("opencode.cli.commands.run.close_database", new_callable=AsyncMock), \
             patch("opencode.cli.commands.run.console"):
            
            with pytest.raises(typer.Exit):
                await _run_async(
                    prompt="Test prompt",
                    model="claude-3-5-sonnet-20241022",
                    provider_name="anthropic",
                    project=MagicMock(),
                    stream=False,
                    system=None,
                )

    @pytest.mark.asyncio
    async def test_run_async_no_provider_config(self, mock_config):
        """Test _run_async when provider config is missing."""
        from opencode.cli.commands.run import _run_async
        import typer
        
        mock_config.get_provider_config = MagicMock(return_value=None)
        
        with patch("opencode.cli.commands.run.Config.load", return_value=mock_config), \
             patch("opencode.cli.commands.run.init_database", new_callable=AsyncMock), \
             patch("opencode.cli.commands.run.close_database", new_callable=AsyncMock), \
             patch("opencode.cli.commands.run.console"):
            
            with pytest.raises(typer.Exit):
                await _run_async(
                    prompt="Test prompt",
                    model="claude-3-5-sonnet-20241022",
                    provider_name="anthropic",
                    project=MagicMock(),
                    stream=False,
                    system=None,
                )

    @pytest.mark.asyncio
    async def test_run_async_unknown_provider(self, mock_config):
        """Test _run_async with unknown provider."""
        from opencode.cli.commands.run import _run_async
        import typer
        
        with patch("opencode.cli.commands.run.Config.load", return_value=mock_config), \
             patch("opencode.cli.commands.run.init_database", new_callable=AsyncMock), \
             patch("opencode.cli.commands.run.close_database", new_callable=AsyncMock), \
             patch("opencode.cli.commands.run.console"):
            
            with pytest.raises(typer.Exit):
                await _run_async(
                    prompt="Test prompt",
                    model="some-model",
                    provider_name="unknown_provider",
                    project=MagicMock(),
                    stream=False,
                    system=None,
                )


class TestServeCommand:
    """Tests for the serve command."""

    def test_serve_command_imports(self):
        """Test that serve command module can be imported."""
        from opencode.cli.commands.serve import serve_command
        assert callable(serve_command)

    def test_serve_command_calls_run_server(self):
        """Test that serve command calls run_server."""
        from opencode.cli.commands.serve import serve_command
        
        with patch("opencode.cli.commands.serve.run_server") as mock_run_server, \
             patch("opencode.cli.commands.serve.console"):
            
            # Call with explicit parameters to avoid typer OptionInfo objects
            serve_command(
                host="127.0.0.1",
                port=3000,
                reload=False,
                workers=1,
            )
            
            mock_run_server.assert_called_once()

    def test_serve_command_custom_params(self):
        """Test serve command with custom parameters."""
        from opencode.cli.commands.serve import serve_command
        
        with patch("opencode.cli.commands.serve.run_server") as mock_run_server, \
             patch("opencode.cli.commands.serve.console"):
            
            serve_command(
                host="0.0.0.0",
                port=8080,
                reload=True,
                workers=4,
            )
            
            # Verify run_server was called
            mock_run_server.assert_called_once()
            call_kwargs = mock_run_server.call_args[1]
            assert call_kwargs["host"] == "0.0.0.0"
            assert call_kwargs["port"] == 8080
            assert call_kwargs["reload"] is True
            assert call_kwargs["workers"] == 4

    def test_serve_command_displays_endpoints(self):
        """Test that serve command displays available endpoints."""
        from opencode.cli.commands.serve import serve_command
        
        with patch("opencode.cli.commands.serve.run_server"), \
             patch("opencode.cli.commands.serve.console") as mock_console:
            
            serve_command(
                host="127.0.0.1",
                port=3000,
                reload=False,
                workers=1,
            )
            
            # Check that console.print was called with endpoint info
            print_calls = [str(call) for call in mock_console.print.call_args_list]
            all_output = " ".join(print_calls)
            
            # Verify key endpoints are mentioned
            assert "/api/health" in all_output or any("/api/health" in str(call) for call in print_calls)
