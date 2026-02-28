"""OAuth flow for MCP (Model Context Protocol) authentication.

Supports OAuth 2.0 Authorization Code flow with PKCE for secure
authentication with MCP servers and external services.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import secrets
import time
import urllib.parse
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

import httpx

from opencode.core.defaults import OAUTH_REDIRECT_URI


class OAuthError(Exception):
    """OAuth authentication error."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        description: Optional[str] = None,
    ):
        super().__init__(message)
        self.error_code = error_code
        self.description = description


class OAuthGrantType(str, Enum):
    """OAuth grant types."""
    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"
    REFRESH_TOKEN = "refresh_token"
    DEVICE_CODE = "urn:ietf:params:oauth:grant-type:device_code"


class OAuthTokenType(str, Enum):
    """OAuth token types."""
    BEARER = "Bearer"
    MAC = "MAC"


@dataclass
class OAuthConfig:
    """OAuth configuration for a provider."""
    client_id: str
    authorization_url: str
    token_url: str
    redirect_uri: str = OAUTH_REDIRECT_URI
    scope: str = ""
    client_secret: Optional[str] = None
    use_pkce: bool = True
    audience: Optional[str] = None
    resource: Optional[str] = None
    
    # Provider-specific settings
    provider_name: str = "oauth"
    revoke_url: Optional[str] = None
    userinfo_url: Optional[str] = None


@dataclass
class OAuthToken:
    """OAuth token response."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    id_token: Optional[str] = None
    expires_at: Optional[float] = None
    
    def __post_init__(self):
        if self.expires_in and not self.expires_at:
            self.expires_at = time.time() + self.expires_in
    
    @property
    def is_expired(self) -> bool:
        """Check if the token is expired."""
        if not self.expires_at:
            return False
        # Consider expired if within 5 minutes of expiration
        return time.time() >= (self.expires_at - 300)
    
    @property
    def authorization_header(self) -> str:
        """Get the Authorization header value."""
        return f"{self.token_type} {self.access_token}"
    
    @classmethod
    def from_response(cls, data: dict[str, Any]) -> "OAuthToken":
        """Create token from OAuth response."""
        return cls(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            expires_in=data.get("expires_in"),
            refresh_token=data.get("refresh_token"),
            scope=data.get("scope"),
            id_token=data.get("id_token"),
        )


@dataclass
class PKCEChallenge:
    """PKCE code verifier and challenge."""
    code_verifier: str
    code_challenge: str
    code_challenge_method: str = "S256"
    
    @classmethod
    def generate(cls) -> "PKCEChallenge":
        """Generate a new PKCE challenge."""
        # Generate random code verifier (43-128 characters)
        code_verifier = secrets.token_urlsafe(96)
        if len(code_verifier) > 128:
            code_verifier = code_verifier[:128]
        
        # Generate code challenge
        challenge_bytes = hashlib.sha256(code_verifier.encode()).digest()
        code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode().rstrip("=")
        
        return cls(
            code_verifier=code_verifier,
            code_challenge=code_challenge,
        )


@dataclass
class DeviceCodeResponse:
    """Device authorization response."""
    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int = 5
    verification_uri_complete: Optional[str] = None
    
    @classmethod
    def from_response(cls, data: dict[str, Any]) -> "DeviceCodeResponse":
        """Create from response data."""
        return cls(
            device_code=data["device_code"],
            user_code=data["user_code"],
            verification_uri=data["verification_uri"],
            expires_in=data["expires_in"],
            interval=data.get("interval", 5),
            verification_uri_complete=data.get("verification_uri_complete"),
        )


class OAuthFlow:
    """OAuth 2.0 authentication flow handler.
    
    Supports:
    - Authorization Code flow with PKCE
    - Device Code flow (for CLI/headless)
    - Client Credentials flow
    - Token refresh
    
    Usage:
        config = OAuthConfig(
            client_id="your-client-id",
            authorization_url="https://auth.example.com/authorize",
            token_url="https://auth.example.com/token",
        )
        
        flow = OAuthFlow(config)
        token = await flow.authorize_with_device_code()
    """
    
    def __init__(
        self,
        config: OAuthConfig,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        """Initialize OAuth flow.
        
        Args:
            config: OAuth configuration
            http_client: Optional HTTP client
        """
        self.config = config
        self._http = http_client or httpx.AsyncClient(timeout=30.0)
        self._owns_client = http_client is None
        self._pkce: Optional[PKCEChallenge] = None
        self._state: Optional[str] = None
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._owns_client:
            await self._http.aclose()
    
    async def __aenter__(self) -> "OAuthFlow":
        return self
    
    async def __aexit__(self, *_args) -> None:
        await self.close()
    
    def _generate_state(self) -> str:
        """Generate a random state parameter."""
        self._state = secrets.token_urlsafe(32)
        return self._state
    
    def get_authorization_url(
        self,
        state: Optional[str] = None,
        additional_params: Optional[dict[str, str]] = None,
    ) -> str:
        """Get the authorization URL for the authorization code flow.
        
        Args:
            state: Optional state parameter (generated if not provided)
            additional_params: Additional query parameters
            
        Returns:
            Authorization URL
        """
        if state:
            self._state = state
        elif not self._state:
            self._generate_state()
        
        # At this point, self._state is guaranteed to be a string
        assert self._state is not None
        
        params: dict[str, str] = {
            "response_type": "code",
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "state": self._state,
        }
        
        if self.config.scope:
            params["scope"] = self.config.scope
        
        if self.config.use_pkce:
            self._pkce = PKCEChallenge.generate()
            params["code_challenge"] = self._pkce.code_challenge
            params["code_challenge_method"] = self._pkce.code_challenge_method
        
        if self.config.audience:
            params["audience"] = self.config.audience
        
        if self.config.resource:
            params["resource"] = self.config.resource
        
        if additional_params:
            params.update(additional_params)
        
        query = urllib.parse.urlencode(params)
        return f"{self.config.authorization_url}?{query}"
    
    async def exchange_code_for_token(
        self,
        code: str,
        state: Optional[str] = None,
    ) -> OAuthToken:
        """Exchange authorization code for access token.
        
        Args:
            code: Authorization code
            state: State parameter for validation
            
        Returns:
            OAuth token
            
        Raises:
            OAuthError: If exchange fails
        """
        # Validate state
        if state and state != self._state:
            raise OAuthError(
                "Invalid state parameter",
                error_code="invalid_state",
            )
        
        data: dict[str, str] = {
            "grant_type": OAuthGrantType.AUTHORIZATION_CODE.value,
            "code": code,
            "redirect_uri": self.config.redirect_uri,
            "client_id": self.config.client_id,
        }
        
        if self.config.client_secret:
            data["client_secret"] = self.config.client_secret
        
        if self._pkce:
            data["code_verifier"] = self._pkce.code_verifier
        
        response = await self._http.post(
            self.config.token_url,
            data=data,
            headers={"Accept": "application/json"},
        )
        
        if response.status_code != 200:
            error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            raise OAuthError(
                f"Token exchange failed: {response.status_code}",
                error_code=error_data.get("error"),
                description=error_data.get("error_description"),
            )
        
        return OAuthToken.from_response(response.json())
    
    async def authorize_with_device_code(
        self,
        device_code_url: Optional[str] = None,
        on_code: Optional[Callable[[DeviceCodeResponse], None]] = None,
    ) -> OAuthToken:
        """Authorize using device code flow.
        
        This is ideal for CLI applications without a browser.
        
        Args:
            device_code_url: URL for device code initiation
            on_code: Callback when device code is received (for displaying to user)
            
        Returns:
            OAuth token
            
        Raises:
            OAuthError: If authorization fails
        """
        # Request device code
        device_url = device_code_url or self.config.token_url.replace("/token", "/device/code")
        
        response = await self._http.post(
            device_url,
            data={
                "client_id": self.config.client_id,
                "scope": self.config.scope,
            },
            headers={"Accept": "application/json"},
        )
        
        if response.status_code != 200:
            error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            raise OAuthError(
                f"Device code request failed: {response.status_code}",
                error_code=error_data.get("error"),
                description=error_data.get("error_description"),
            )
        
        device_code = DeviceCodeResponse.from_response(response.json())
        
        # Notify user
        if on_code:
            on_code(device_code)
        else:
            print(f"\nTo authenticate, visit: {device_code.verification_uri}")
            print(f"Enter code: {device_code.user_code}\n")
        
        # Poll for token
        start_time = time.time()
        while time.time() - start_time < device_code.expires_in:
            await asyncio.sleep(device_code.interval)
            
            try:
                token_response = await self._http.post(
                    self.config.token_url,
                    data={
                        "grant_type": OAuthGrantType.DEVICE_CODE.value,
                        "device_code": device_code.device_code,
                        "client_id": self.config.client_id,
                    },
                    headers={"Accept": "application/json"},
                )
                
                if token_response.status_code == 200:
                    return OAuthToken.from_response(token_response.json())
                
                error_data = token_response.json()
                error_code = error_data.get("error")
                
                if error_code == "authorization_pending":
                    continue
                elif error_code == "slow_down":
                    device_code.interval += 5
                    continue
                elif error_code == "expired_token":
                    raise OAuthError(
                        "Device code expired",
                        error_code=error_code,
                    )
                else:
                    raise OAuthError(
                        f"Authorization failed: {error_code}",
                        error_code=error_code,
                        description=error_data.get("error_description"),
                    )
                    
            except httpx.HTTPError as e:
                raise OAuthError(f"HTTP error: {e}")
        
        raise OAuthError("Device code authorization timed out")
    
    async def client_credentials_flow(self) -> OAuthToken:
        """Perform client credentials flow.
        
        This is for server-to-server authentication.
        
        Returns:
            OAuth token
        """
        data: dict[str, str] = {
            "grant_type": OAuthGrantType.CLIENT_CREDENTIALS.value,
            "client_id": self.config.client_id,
        }
        
        if self.config.client_secret:
            data["client_secret"] = self.config.client_secret
        
        if self.config.scope:
            data["scope"] = self.config.scope
        
        if self.config.audience:
            data["audience"] = self.config.audience
        
        response = await self._http.post(
            self.config.token_url,
            data=data,
            headers={"Accept": "application/json"},
        )
        
        if response.status_code != 200:
            error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            raise OAuthError(
                f"Client credentials flow failed: {response.status_code}",
                error_code=error_data.get("error"),
                description=error_data.get("error_description"),
            )
        
        return OAuthToken.from_response(response.json())
    
    async def refresh_token(self, refresh_token: str) -> OAuthToken:
        """Refresh an access token.
        
        Args:
            refresh_token: The refresh token
            
        Returns:
            New OAuth token
        """
        data: dict[str, str] = {
            "grant_type": OAuthGrantType.REFRESH_TOKEN.value,
            "refresh_token": refresh_token,
            "client_id": self.config.client_id,
        }
        
        if self.config.client_secret:
            data["client_secret"] = self.config.client_secret
        
        response = await self._http.post(
            self.config.token_url,
            data=data,
            headers={"Accept": "application/json"},
        )
        
        if response.status_code != 200:
            error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            raise OAuthError(
                f"Token refresh failed: {response.status_code}",
                error_code=error_data.get("error"),
                description=error_data.get("error_description"),
            )
        
        return OAuthToken.from_response(response.json())
    
    async def revoke_token(self, token: str) -> bool:
        """Revoke a token.
        
        Args:
            token: Token to revoke
            
        Returns:
            True if revoked successfully
        """
        if not self.config.revoke_url:
            return False
        
        response = await self._http.post(
            self.config.revoke_url,
            data={
                "token": token,
                "client_id": self.config.client_id,
            },
            headers={"Accept": "application/json"},
        )
        
        return response.status_code in (200, 204)
    
    async def get_userinfo(self, token: OAuthToken) -> dict[str, Any]:
        """Get user information from the provider.
        
        Args:
            token: OAuth token
            
        Returns:
            User information dictionary
        """
        if not self.config.userinfo_url:
            raise OAuthError("Userinfo URL not configured")
        
        response = await self._http.get(
            self.config.userinfo_url,
            headers={
                "Authorization": token.authorization_header,
                "Accept": "application/json",
            },
        )
        
        if response.status_code != 200:
            raise OAuthError(f"Userinfo request failed: {response.status_code}")
        
        return response.json()


# Pre-configured OAuth providers
OAUTH_PROVIDERS: dict[str, OAuthConfig] = {
    "github": OAuthConfig(
        provider_name="github",
        client_id="",  # Set by user
        authorization_url="https://github.com/login/oauth/authorize",
        token_url="https://github.com/login/oauth/access_token",
        scope="repo user",
        userinfo_url="https://api.github.com/user",
    ),
    "google": OAuthConfig(
        provider_name="google",
        client_id="",  # Set by user
        authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        scope="openid email profile",
        userinfo_url="https://openidconnect.googleapis.com/v1/userinfo",
    ),
    "microsoft": OAuthConfig(
        provider_name="microsoft",
        client_id="",  # Set by user
        authorization_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
        scope="openid email profile",
        userinfo_url="https://graph.microsoft.com/v1.0/me",
    ),
    "anthropic": OAuthConfig(
        provider_name="anthropic",
        client_id="",  # Set by user
        authorization_url="https://auth.anthropic.com/authorize",
        token_url="https://auth.anthropic.com/oauth/token",
        scope="openid profile",
    ),
    "auth0": OAuthConfig(
        provider_name="auth0",
        client_id="",  # Set by user
        authorization_url="",  # Set by user: https://{domain}/authorize
        token_url="",  # Set by user: https://{domain}/oauth/token
        scope="openid profile email",
    ),
}


def get_oauth_config(provider: str) -> Optional[OAuthConfig]:
    """Get OAuth configuration for a provider.
    
    Args:
        provider: Provider name
        
        Returns:
        OAuth configuration or None if not found
    """
    return OAUTH_PROVIDERS.get(provider)


def register_oauth_provider(name: str, config: OAuthConfig) -> None:
    """Register a custom OAuth provider.
    
    Args:
        name: Provider name
        config: OAuth configuration
    """
    OAUTH_PROVIDERS[name] = config
