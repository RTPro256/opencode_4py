"""
Tests for OllamaClient.
"""

import json
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from opencode.llmchecker.ollama.client import OllamaClient
from opencode.llmchecker.ollama.models import (
    OllamaModel,
    OllamaResponse,
    OllamaRunningModel,
    OllamaVersion,
    OllamaPullProgress,
)


class TestOllamaClientInit:
    """Tests for OllamaClient initialization."""

    def test_init_default_url(self):
        """Test initialization with default URL."""
        client = OllamaClient()
        assert client.base_url == "http://localhost:11434"

    def test_init_custom_url(self):
        """Test initialization with custom URL."""
        client = OllamaClient(base_url="http://custom:8080")
        assert client.base_url == "http://custom:8080"

    def test_init_url_normalization(self):
        """Test URL normalization."""
        client = OllamaClient(base_url="localhost:11434")
        assert client.base_url == "http://localhost:11434"

    def test_init_url_trailing_slash(self):
        """Test URL trailing slash removal."""
        client = OllamaClient(base_url="http://localhost:11434/")
        assert client.base_url == "http://localhost:11434"

    def test_init_with_env_var(self):
        """Test initialization with OLLAMA_HOST env var."""
        with patch.dict("os.environ", {"OLLAMA_HOST": "http://env-host:1234"}):
            client = OllamaClient()
            assert client.base_url == "http://env-host:1234"

    def test_init_ollama_url_env_var(self):
        """Test initialization with OLLAMA_URL env var."""
        with patch.dict("os.environ", {"OLLAMA_URL": "http://ollama-url:5678"}, clear=True):
            # Clear OLLAMA_HOST to test OLLAMA_URL fallback
            env = {"OLLAMA_URL": "http://ollama-url:5678"}
            with patch.dict("os.environ", env, clear=True):
                client = OllamaClient()
                assert client.base_url == "http://ollama-url:5678"


class TestOllamaClientAvailability:
    """Tests for OllamaClient availability checking."""

    @pytest.fixture
    def client(self):
        """Create a client instance."""
        return OllamaClient()

    @pytest.mark.asyncio
    async def test_check_availability_success(self, client):
        """Test successful availability check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"version": "0.1.0"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await client.check_availability(force=True)

            assert result["available"] is True
            assert result["version"] == "0.1.0"

    @pytest.mark.asyncio
    async def test_check_availability_cached(self, client):
        """Test cached availability check."""
        client._is_available = {"available": True, "version": "0.1.0"}
        client._last_check = time.time()

        result = await client.check_availability(force=False)
        assert result["available"] is True

    @pytest.mark.asyncio
    async def test_check_availability_cache_expired(self, client):
        """Test expired cache triggers new check."""
        client._is_available = {"available": True, "version": "old"}
        client._last_check = time.time() - 60  # Expired

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"version": "0.2.0"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await client.check_availability(force=False)

            assert result["version"] == "0.2.0"

    @pytest.mark.asyncio
    async def test_check_availability_http_error(self, client):
        """Test availability check with HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await client.check_availability(force=True)

            assert result["available"] is False
            assert "HTTP 500" in result["error"]

    @pytest.mark.asyncio
    async def test_check_availability_connection_error(self, client):
        """Test availability check with connection error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await client.check_availability(force=True)

            assert result["available"] is False
            assert "Cannot connect" in result["error"]

    @pytest.mark.asyncio
    async def test_check_availability_timeout(self, client):
        """Test availability check with timeout."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await client.check_availability(force=True)

            assert result["available"] is False
            assert "timeout" in result["error"].lower()


class TestOllamaClientVersion:
    """Tests for OllamaClient version methods."""

    @pytest.fixture
    def client(self):
        """Create a client instance."""
        return OllamaClient()

    @pytest.mark.asyncio
    async def test_get_version_success(self, client):
        """Test successful version retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"version": "0.1.20"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await client.get_version()

            assert result is not None
            assert result.version == "0.1.20"

    @pytest.mark.asyncio
    async def test_get_version_failure(self, client):
        """Test version retrieval failure."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=Exception("Failed"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await client.get_version()

            assert result is None


class TestOllamaClientModels:
    """Tests for OllamaClient model methods."""

    @pytest.fixture
    def client(self):
        """Create a client instance."""
        client = OllamaClient()
        client._is_available = {"available": True}
        client._last_check = time.time()
        return client

    @pytest.mark.asyncio
    async def test_list_models_success(self, client):
        """Test successful model listing."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {
                    "name": "llama3:latest",
                    "size": 4661224676,
                    "digest": "abc123",
                    "modified_at": "2024-01-01T00:00:00Z",
                    "details": {"family": "llama"},
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            models = await client.list_models()

            assert len(models) == 1
            assert models[0].name == "llama3:latest"

    @pytest.mark.asyncio
    async def test_list_models_not_available(self, client):
        """Test model listing when Ollama not available."""
        client._is_available = {"available": False, "error": "Not running"}

        with pytest.raises(ConnectionError):
            await client.list_models()

    @pytest.mark.asyncio
    async def test_get_running_models_success(self, client):
        """Test successful running model listing."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {
                    "name": "llama3:latest",
                    "model": "llama3:latest",
                    "size": 4661224676,
                    "digest": "abc123",
                    "expires_at": "2024-01-01T01:00:00Z",
                    "size_vram": 4000000000,
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            models = await client.get_running_models()

            assert len(models) == 1
            assert models[0].name == "llama3:latest"

    @pytest.mark.asyncio
    async def test_get_running_models_not_available(self, client):
        """Test running models when Ollama not available."""
        client._is_available = {"available": False}

        models = await client.get_running_models()
        assert models == []


class TestOllamaClientPull:
    """Tests for OllamaClient pull methods."""

    @pytest.fixture
    def client(self):
        """Create a client instance."""
        return OllamaClient()

    @pytest.mark.asyncio
    async def test_pull_model_success(self, client):
        """Test successful model pull."""
        progress_lines = [
            '{"status": "pulling manifest"}',
            '{"status": "downloading", "digest": "abc", "total": 100, "completed": 50}',
            '{"status": "complete"}',
        ]

        async def mock_aiter_lines():
            for line in progress_lines:
                yield line

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.aiter_lines = mock_aiter_lines

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.stream = MagicMock(return_value=mock_response)
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            progress_list = []
            async for progress in client.pull_model("llama3"):
                progress_list.append(progress)

            assert len(progress_list) == 3
            assert progress_list[0].status == "pulling manifest"

    @pytest.mark.asyncio
    async def test_pull_huggingface_model(self, client):
        """Test pulling Hugging Face model."""
        progress_lines = [
            '{"status": "pulling from Hugging Face"}',
        ]

        async def mock_aiter_lines():
            for line in progress_lines:
                yield line

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.aiter_lines = mock_aiter_lines

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.stream = MagicMock(return_value=mock_response)
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            progress_list = []
            async for progress in client.pull_huggingface_model("user", "repo", "Q4_K_M"):
                progress_list.append(progress)

            assert len(progress_list) == 1


class TestOllamaClientModelNameNormalization:
    """Tests for model name normalization."""

    @pytest.fixture
    def client(self):
        """Create a client instance."""
        return OllamaClient()

    def test_normalize_standard_model(self, client):
        """Test normalizing standard model name."""
        result = client._normalize_model_name("llama3:latest")
        assert result == "llama3:latest"

    def test_normalize_huggingface_model(self, client):
        """Test normalizing Hugging Face model name."""
        result = client._normalize_model_name("hf.co/user/repo")
        assert result == "hf.co/user/repo"

    def test_normalize_huggingface_co_model(self, client):
        """Test normalizing huggingface.co prefix."""
        result = client._normalize_model_name("huggingface.co/user/repo")
        assert result == "hf.co/user/repo"

    def test_normalize_at_prefix_model(self, client):
        """Test normalizing @ prefix model name."""
        result = client._normalize_model_name("@user/repo")
        assert result == "hf.co/user/repo"

    def test_is_huggingface_model(self, client):
        """Test checking if model is from Hugging Face."""
        assert client.is_huggingface_model("hf.co/user/repo") is True
        assert client.is_huggingface_model("huggingface.co/user/repo") is True
        assert client.is_huggingface_model("@user/repo") is True
        assert client.is_huggingface_model("llama3:latest") is False

    def test_parse_huggingface_model(self, client):
        """Test parsing Hugging Face model name."""
        result = client.parse_huggingface_model("hf.co/user/repo:Q4_K_M")

        assert result["username"] == "user"
        assert result["repository"] == "repo"
        assert result["quantization"] == "Q4_K_M"
        assert result["full_name"] == "user/repo"

    def test_parse_huggingface_model_no_quantization(self, client):
        """Test parsing Hugging Face model without quantization."""
        result = client.parse_huggingface_model("hf.co/user/repo")

        assert result["username"] == "user"
        assert result["repository"] == "repo"
        assert result["quantization"] is None

    def test_parse_non_huggingface_model(self, client):
        """Test parsing non-Hugging Face model."""
        result = client.parse_huggingface_model("llama3:latest")
        assert result == {}


class TestOllamaClientDelete:
    """Tests for model deletion."""

    @pytest.fixture
    def client(self):
        """Create a client instance."""
        return OllamaClient()

    @pytest.mark.asyncio
    async def test_delete_model_success(self, client):
        """Test successful model deletion."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await client.delete_model("llama3:latest")
            assert result is True

    @pytest.mark.asyncio
    async def test_delete_model_failure(self, client):
        """Test failed model deletion."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await client.delete_model("nonexistent")
            assert result is False

    @pytest.mark.asyncio
    async def test_delete_model_exception(self, client):
        """Test model deletion with exception."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.request = AsyncMock(side_effect=Exception("Failed"))
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await client.delete_model("llama3")
            assert result is False


class TestOllamaClientGenerate:
    """Tests for generation methods."""

    @pytest.fixture
    def client(self):
        """Create a client instance."""
        return OllamaClient()

    @pytest.mark.asyncio
    async def test_generate_success(self, client):
        """Test successful generation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "llama3",
            "response": "Hello, world!",
            "done": True,
            "total_duration": 1000000000,
            "load_duration": 100000000,
            "prompt_eval_count": 10,
            "prompt_eval_duration": 500000000,
            "eval_count": 5,
            "eval_duration": 400000000,
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await client.generate("llama3", "Hello")

            assert result.model == "llama3"
            assert result.content == "Hello, world!"
            assert result.done is True

    @pytest.mark.asyncio
    async def test_generate_with_options(self, client):
        """Test generation with options."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "model": "llama3",
            "response": "Response",
            "done": True,
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await client.generate(
                "llama3",
                "Hello",
                system="Be helpful",
                format="json",
                options={"temperature": 0.7}
            )

            assert result.content == "Response"
            # Verify the payload included the options
            call_args = mock_instance.post.call_args
            payload = call_args.kwargs["json"]
            assert payload["system"] == "Be helpful"
            assert payload["format"] == "json"
            assert payload["options"]["temperature"] == 0.7

    @pytest.mark.asyncio
    async def test_generate_failure(self, client):
        """Test generation failure."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal error"

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            with pytest.raises(RuntimeError):
                await client.generate("llama3", "Hello")


class TestOllamaClientChat:
    """Tests for chat methods."""

    @pytest.fixture
    def client(self):
        """Create a client instance."""
        return OllamaClient()

    @pytest.mark.asyncio
    async def test_chat_success(self, client):
        """Test successful chat."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {"role": "assistant", "content": "Hi there!"},
            "done": True,
            "total_duration": 1000000000,
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            messages = [{"role": "user", "content": "Hello"}]
            result = await client.chat("llama3", messages)

            assert result.content == "Hi there!"

    @pytest.mark.asyncio
    async def test_chat_failure(self, client):
        """Test chat failure."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Error"

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            with pytest.raises(RuntimeError):
                await client.chat("llama3", [{"role": "user", "content": "Hi"}])


class TestOllamaClientEmbed:
    """Tests for embedding methods."""

    @pytest.fixture
    def client(self):
        """Create a client instance."""
        return OllamaClient()

    @pytest.mark.asyncio
    async def test_embed_single(self, client):
        """Test single text embedding."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embeddings": [[0.1, 0.2, 0.3]]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await client.embed("nomic-embed-text", "Hello")

            assert result == [[0.1, 0.2, 0.3]]

    @pytest.mark.asyncio
    async def test_embed_multiple(self, client):
        """Test multiple text embeddings."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embeddings": [[0.1, 0.2], [0.3, 0.4]]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await client.embed("nomic-embed-text", ["Hello", "World"])

            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_embed_failure(self, client):
        """Test embedding failure."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Error"

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            with pytest.raises(RuntimeError):
                await client.embed("nomic-embed-text", "Hello")


class TestOllamaClientShowModel:
    """Tests for show_model method."""

    @pytest.fixture
    def client(self):
        """Create a client instance."""
        return OllamaClient()

    @pytest.mark.asyncio
    async def test_show_model_success(self, client):
        """Test successful model info retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "license": "MIT",
            "modelfile": "FROM llama3",
            "parameters": {"temperature": 0.7},
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await client.show_model("llama3")

            assert result["license"] == "MIT"

    @pytest.mark.asyncio
    async def test_show_model_failure(self, client):
        """Test model info retrieval failure."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not found"

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            with pytest.raises(RuntimeError):
                await client.show_model("nonexistent")


class TestOllamaClientTestConnection:
    """Tests for test_connection method."""

    @pytest.fixture
    def client(self):
        """Create a client instance."""
        return OllamaClient()

    @pytest.mark.asyncio
    async def test_connection_success(self, client):
        """Test successful connection test."""
        mock_version_response = MagicMock()
        mock_version_response.status_code = 200
        mock_version_response.json.return_value = {"version": "0.1.0"}

        mock_models_response = MagicMock()
        mock_models_response.status_code = 200
        mock_models_response.json.return_value = {
            "models": [{"name": "llama3:latest"}]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(side_effect=[mock_version_response, mock_models_response])
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            result = await client.test_connection()

            assert result["available"] is True
            assert result["models_found"] == 1


class TestOllamaClientParseMethods:
    """Tests for parsing methods."""

    @pytest.fixture
    def client(self):
        """Create a client instance."""
        return OllamaClient()

    def test_parse_model(self, client):
        """Test parsing model data."""
        data = {
            "name": "llama3:latest",
            "size": 4661224676,
            "digest": "abc123",
            "modified_at": "2024-01-01T00:00:00Z",
            "details": {"family": "llama"},
        }

        model = client._parse_model(data)

        assert model.name == "llama3:latest"
        assert model.size == 4661224676
        assert model.digest == "abc123"
        assert model.details == {"family": "llama"}

    def test_parse_model_invalid_date(self, client):
        """Test parsing model with invalid date."""
        data = {
            "name": "llama3",
            "size": 1000,
            "modified_at": "invalid-date",
        }

        model = client._parse_model(data)

        assert model.name == "llama3"
        assert model.modified_at is None

    def test_parse_running_model(self, client):
        """Test parsing running model data."""
        data = {
            "name": "llama3:latest",
            "model": "llama3:latest",
            "size": 4661224676,
            "digest": "abc123",
            "expires_at": "2024-01-01T01:00:00Z",
            "size_vram": 4000000000,
        }

        model = client._parse_running_model(data)

        assert model.name == "llama3:latest"
        assert model.size_vram == 4000000000

    def test_parse_response(self, client):
        """Test parsing response data."""
        data = {
            "model": "llama3",
            "response": "Hello!",
            "done": True,
            "total_duration": 1000000000,
            "eval_count": 5,
        }

        response = client._parse_response(data)

        assert response.model == "llama3"
        assert response.content == "Hello!"
        assert response.eval_count == 5
