"""
Extended tests for OAuth module.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import time

from opencode.mcp.oauth import (
    OAuthError,
    OAuthGrantType,
    OAuthTokenType,
    OAuthConfig,
    OAuthToken,
    PKCEChallenge,
    DeviceCodeResponse,
    OAuthFlow,
)


class TestOAuthError:
    """Tests for OAuthError class."""

    def test_init_basic(self):
        """Test basic error initialization."""
        error = OAuthError("Test error")
        assert str(error) == "Test error"
        assert error.error_code is None
        assert error.description is None

    def test_init_with_code(self):
        """Test error with error code."""
        error = OAuthError("Test error", error_code="invalid_request")
        assert str(error) == "Test error"
        assert error.error_code == "invalid_request"
        assert error.description is None

    def test_init_with_all(self):
        """Test error with all fields."""
        error = OAuthError(
            "Test error",
            error_code="invalid_request",
            description="Missing required parameter"
        )
        assert str(error) == "Test error"
        assert error.error_code == "invalid_request"
        assert error.description == "Missing required parameter"


class TestOAuthGrantType:
    """Tests for OAuthGrantType enum."""

    def test_authorization_code(self):
        """Test authorization code grant type."""
        assert OAuthGrantType.AUTHORIZATION_CODE.value == "authorization_code"

    def test_client_credentials(self):
        """Test client credentials grant type."""
        assert OAuthGrantType.CLIENT_CREDENTIALS.value == "client_credentials"

    def test_refresh_token(self):
        """Test refresh token grant type."""
        assert OAuthGrantType.REFRESH_TOKEN.value == "refresh_token"

    def test_device_code(self):
        """Test device code grant type."""
        assert OAuthGrantType.DEVICE_CODE.value == "urn:ietf:params:oauth:grant-type:device_code"


class TestOAuthTokenType:
    """Tests for OAuthTokenType enum."""

    def test_bearer(self):
        """Test bearer token type."""
        assert OAuthTokenType.BEARER.value == "Bearer"

    def test_mac(self):
        """Test MAC token type."""
        assert OAuthTokenType.MAC.value == "MAC"


class TestOAuthConfig:
    """Tests for OAuthConfig dataclass."""

    def test_init_required_fields(self):
        """Test initialization with required fields only."""
        config = OAuthConfig(
            client_id="test-client",
            authorization_url="https://auth.example.com/authorize",
            token_url="https://auth.example.com/token",
        )
        assert config.client_id == "test-client"
        assert config.authorization_url == "https://auth.example.com/authorize"
        assert config.token_url == "https://auth.example.com/token"
        assert config.redirect_uri == "http://localhost:8080/callback"
        assert config.scope == ""
        assert config.client_secret is None
        assert config.use_pkce is True

    def test_init_all_fields(self):
        """Test initialization with all fields."""
        config = OAuthConfig(
            client_id="test-client",
            authorization_url="https://auth.example.com/authorize",
            token_url="https://auth.example.com/token",
            redirect_uri="https://app.example.com/callback",
            scope="read write",
            client_secret="secret",
            use_pkce=False,
            audience="api.example.com",
            resource="resource.example.com",
            provider_name="test_provider",
            revoke_url="https://auth.example.com/revoke",
            userinfo_url="https://auth.example.com/userinfo",
        )
        assert config.client_id == "test-client"
        assert config.redirect_uri == "https://app.example.com/callback"
        assert config.scope == "read write"
        assert config.client_secret == "secret"
        assert config.use_pkce is False
        assert config.audience == "api.example.com"
        assert config.resource == "resource.example.com"
        assert config.provider_name == "test_provider"
        assert config.revoke_url == "https://auth.example.com/revoke"
        assert config.userinfo_url == "https://auth.example.com/userinfo"


class TestOAuthToken:
    """Tests for OAuthToken dataclass."""

    def test_init_basic(self):
        """Test basic token initialization."""
        token = OAuthToken(access_token="test-token")
        assert token.access_token == "test-token"
        assert token.token_type == "Bearer"
        assert token.expires_in is None
        assert token.refresh_token is None
        assert token.scope is None
        assert token.id_token is None
        assert token.expires_at is None

    def test_init_with_expires_in(self):
        """Test token with expires_in calculates expires_at."""
        with patch("opencode.mcp.oauth.time.time", return_value=1000):
            token = OAuthToken(access_token="test-token", expires_in=3600)
            assert token.expires_at == 4600  # 1000 + 3600

    def test_init_with_expires_at(self):
        """Test token with explicit expires_at."""
        token = OAuthToken(access_token="test-token", expires_at=5000)
        assert token.expires_at == 5000

    def test_is_expired_no_expiry(self):
        """Test is_expired when no expiry set."""
        token = OAuthToken(access_token="test-token")
        assert token.is_expired is False

    def test_is_expired_not_expired(self):
        """Test is_expired when not expired."""
        with patch("opencode.mcp.oauth.time.time", return_value=1000):
            token = OAuthToken(access_token="test-token", expires_at=5000)
            assert token.is_expired is False

    def test_is_expired_expired(self):
        """Test is_expired when expired."""
        with patch("opencode.mcp.oauth.time.time", return_value=5000):
            # Token expires at 1000, with 5 min buffer, expired after 700
            token = OAuthToken(access_token="test-token", expires_at=1000)
            assert token.is_expired is True

    def test_is_expired_within_buffer(self):
        """Test is_expired within 5 minute buffer."""
        with patch("opencode.mcp.oauth.time.time", return_value=400):
            # Token expires at 500, with 5 min (300s) buffer, expired at 200
            # Current time 400 > 200, so it's expired
            token = OAuthToken(access_token="test-token", expires_at=500)
            assert token.is_expired is True

    def test_authorization_header(self):
        """Test authorization header generation."""
        token = OAuthToken(access_token="test-token", token_type="Bearer")
        assert token.authorization_header == "Bearer test-token"

    def test_authorization_header_custom_type(self):
        """Test authorization header with custom token type."""
        token = OAuthToken(access_token="test-token", token_type="MAC")
        assert token.authorization_header == "MAC test-token"

    def test_from_response_minimal(self):
        """Test creating token from minimal response."""
        token = OAuthToken.from_response({"access_token": "test-token"})
        assert token.access_token == "test-token"
        assert token.token_type == "Bearer"

    def test_from_response_full(self):
        """Test creating token from full response."""
        with patch("opencode.mcp.oauth.time.time", return_value=1000):
            token = OAuthToken.from_response({
                "access_token": "test-token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": "refresh-token",
                "scope": "read write",
                "id_token": "id-token",
            })
            assert token.access_token == "test-token"
            assert token.token_type == "Bearer"
            assert token.expires_in == 3600
            assert token.refresh_token == "refresh-token"
            assert token.scope == "read write"
            assert token.id_token == "id-token"


class TestPKCEChallenge:
    """Tests for PKCEChallenge class."""

    def test_generate(self):
        """Test PKCE challenge generation."""
        challenge = PKCEChallenge.generate()
        
        assert challenge.code_verifier is not None
        assert challenge.code_challenge is not None
        assert challenge.code_challenge_method == "S256"
        
        # Verifier should be 43-128 characters
        assert 43 <= len(challenge.code_verifier) <= 128
        
        # Challenge should be different from verifier
        assert challenge.code_challenge != challenge.code_verifier

    def test_generate_unique(self):
        """Test that each generation is unique."""
        challenge1 = PKCEChallenge.generate()
        challenge2 = PKCEChallenge.generate()
        
        assert challenge1.code_verifier != challenge2.code_verifier
        assert challenge1.code_challenge != challenge2.code_challenge

    def test_manual_creation(self):
        """Test manually creating a PKCE challenge."""
        challenge = PKCEChallenge(
            code_verifier="test-verifier",
            code_challenge="test-challenge",
            code_challenge_method="plain",
        )
        assert challenge.code_verifier == "test-verifier"
        assert challenge.code_challenge == "test-challenge"
        assert challenge.code_challenge_method == "plain"


class TestDeviceCodeResponse:
    """Tests for DeviceCodeResponse class."""

    def test_from_response_minimal(self):
        """Test creating from minimal response."""
        response = DeviceCodeResponse.from_response({
            "device_code": "device-123",
            "user_code": "ABCD-1234",
            "verification_uri": "https://auth.example.com/device",
            "expires_in": 900,
        })
        
        assert response.device_code == "device-123"
        assert response.user_code == "ABCD-1234"
        assert response.verification_uri == "https://auth.example.com/device"
        assert response.expires_in == 900
        assert response.interval == 5
        assert response.verification_uri_complete is None

    def test_from_response_full(self):
        """Test creating from full response."""
        response = DeviceCodeResponse.from_response({
            "device_code": "device-123",
            "user_code": "ABCD-1234",
            "verification_uri": "https://auth.example.com/device",
            "expires_in": 900,
            "interval": 10,
            "verification_uri_complete": "https://auth.example.com/device?code=ABCD-1234",
        })
        
        assert response.device_code == "device-123"
        assert response.user_code == "ABCD-1234"
        assert response.verification_uri == "https://auth.example.com/device"
        assert response.expires_in == 900
        assert response.interval == 10
        assert response.verification_uri_complete == "https://auth.example.com/device?code=ABCD-1234"


class TestOAuthFlow:
    """Tests for OAuthFlow class."""

    @pytest.fixture
    def config(self):
        """Create a test OAuth config."""
        return OAuthConfig(
            client_id="test-client",
            authorization_url="https://auth.example.com/authorize",
            token_url="https://auth.example.com/token",
            scope="read write",
        )

    def test_init(self, config):
        """Test OAuthFlow initialization."""
        flow = OAuthFlow(config)
        assert flow.config == config
        assert flow._pkce is None
        assert flow._state is None

    def test_init_with_client(self, config):
        """Test OAuthFlow initialization with custom HTTP client."""
        client = MagicMock()
        flow = OAuthFlow(config, http_client=client)
        assert flow._http == client
        assert flow._owns_client is False

    @pytest.mark.asyncio
    async def test_close(self, config):
        """Test closing the flow."""
        flow = OAuthFlow(config)
        await flow.close()

    @pytest.mark.asyncio
    async def test_context_manager(self, config):
        """Test using OAuthFlow as context manager."""
        async with OAuthFlow(config) as flow:
            assert flow is not None

    def test_generate_state(self, config):
        """Test state generation."""
        flow = OAuthFlow(config)
        state = flow._generate_state()
        
        assert state is not None
        assert flow._state == state
        # State should be URL-safe
        assert all(c.isalnum() or c in "-_" for c in state)

    def test_get_authorization_url_basic(self, config):
        """Test getting authorization URL."""
        flow = OAuthFlow(config)
        url = flow.get_authorization_url()
        
        assert "https://auth.example.com/authorize" in url
        assert "client_id=test-client" in url
        assert "response_type=code" in url
        assert "redirect_uri=" in url
        assert "state=" in url
        assert "scope=read+write" in url or "scope=read%20write" in url

    def test_get_authorization_url_with_state(self, config):
        """Test getting authorization URL with custom state."""
        flow = OAuthFlow(config)
        url = flow.get_authorization_url(state="custom-state")
        
        assert "state=custom-state" in url
        assert flow._state == "custom-state"

    def test_get_authorization_url_with_pkce(self, config):
        """Test getting authorization URL with PKCE."""
        flow = OAuthFlow(config)
        url = flow.get_authorization_url()
        
        # PKCE is enabled by default
        assert "code_challenge=" in url
        assert "code_challenge_method=S256" in url
        assert flow._pkce is not None

    def test_get_authorization_url_without_pkce(self):
        """Test getting authorization URL without PKCE."""
        config = OAuthConfig(
            client_id="test-client",
            authorization_url="https://auth.example.com/authorize",
            token_url="https://auth.example.com/token",
            use_pkce=False,
        )
        flow = OAuthFlow(config)
        url = flow.get_authorization_url()
        
        assert "code_challenge=" not in url

    def test_get_authorization_url_with_audience(self):
        """Test getting authorization URL with audience."""
        config = OAuthConfig(
            client_id="test-client",
            authorization_url="https://auth.example.com/authorize",
            token_url="https://auth.example.com/token",
            audience="api.example.com",
        )
        flow = OAuthFlow(config)
        url = flow.get_authorization_url()
        
        assert "audience=api.example.com" in url

    def test_get_authorization_url_with_additional_params(self, config):
        """Test getting authorization URL with additional params."""
        flow = OAuthFlow(config)
        url = flow.get_authorization_url(additional_params={"prompt": "consent"})
        
        assert "prompt=consent" in url

    @pytest.mark.asyncio
    async def test_close_owns_client(self, config):
        """Test close when flow owns the client."""
        flow = OAuthFlow(config)
        assert flow._owns_client is True
        
        # Should close the internal client
        with patch.object(flow._http, "aclose", new_callable=AsyncMock) as mock_close:
            await flow.close()
            mock_close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_does_not_own_client(self, config):
        """Test close when flow does not own the client."""
        client = MagicMock()
        client.aclose = AsyncMock()
        flow = OAuthFlow(config, http_client=client)
        assert flow._owns_client is False
        
        await flow.close()
        client.aclose.assert_not_called()
