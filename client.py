"""Async HTTP client for Classavo API."""

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

from config import config

logger = logging.getLogger(__name__)


class ClassavoClient:
    """Async HTTP client for Classavo API with rate limiting and auth."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_token: Optional[str] = None,
    ):
        self._api_url = (api_url or config.api_url).rstrip("/")
        self._api_token = api_token or config.api_token
        self._rate_limit = config.rate_limit
        self._last_request_time = 0.0

    @classmethod
    def from_context(cls, ctx=None) -> "ClassavoClient":
        """Create client from MCP context or use default config."""
        # If context has a token, use it (per-user auth)
        if ctx and hasattr(ctx, "token") and ctx.token:
            return cls(api_token=ctx.token)
        return cls()

    async def _rate_limit_request(self) -> None:
        """Enforce rate limiting between API calls."""
        if self._rate_limit > 0:
            loop = asyncio.get_event_loop()
            current_time = loop.time()
            time_since_last = current_time - self._last_request_time
            min_interval = 1.0 / self._rate_limit
            if time_since_last < min_interval:
                await asyncio.sleep(min_interval - time_since_last)
            self._last_request_time = loop.time()

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self._api_token:
            # Django Token authentication format
            headers["Authorization"] = f"Token {self._api_token}"
        return headers

    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate with username/password and store token.

        Args:
            username: Email or phone number
            password: User password

        Returns:
            Dict with token on success
        """
        await self._rate_limit_request()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._api_url}/api/login",
                json={"username": username, "password": password},
                headers={"Content-Type": "application/json"},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            # Store the token for future requests
            if "token" in data:
                self._api_token = data["token"]
                logger.info("Successfully authenticated with Classavo API")

            return data

    async def logout(self) -> Dict[str, Any]:
        """Logout and invalidate current token."""
        result = await self.post("/api/logout")
        self._api_token = None
        return result

    async def request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make an authenticated API request.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            endpoint: API endpoint (e.g., "/api/v2/courses/")
            data: Request body (for POST, PUT, PATCH)
            params: Query parameters

        Returns:
            Response JSON data
        """
        await self._rate_limit_request()

        url = f"{self._api_url}{endpoint}"
        headers = self._get_headers()

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method.upper(),
                    url=url,
                    headers=headers,
                    json=data,
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()

                # Handle empty responses
                if response.status_code == 204 or not response.content:
                    return {"status": "success"}

                # Handle non-JSON responses
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    return response.json()
                else:
                    return {"status": "success", "message": response.text}

            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Request failed: {str(e)}")
                raise

    # Convenience methods
    async def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a GET request."""
        return await self.request("GET", endpoint, params=params)

    async def post(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a POST request."""
        return await self.request("POST", endpoint, data=data)

    async def put(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a PUT request."""
        return await self.request("PUT", endpoint, data=data)

    async def patch(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a PATCH request."""
        return await self.request("PATCH", endpoint, data=data)

    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """Make a DELETE request."""
        return await self.request("DELETE", endpoint)

    async def get_current_user(self) -> Dict[str, Any]:
        """Get current authenticated user info."""
        return await self.get("/api/me")

    async def verify_token(self) -> bool:
        """Verify if the current token is valid."""
        if not self._api_token:
            return False
        try:
            await self.get_current_user()
            return True
        except Exception:
            return False

    @property
    def is_authenticated(self) -> bool:
        """Check if client has a token (doesn't verify validity)."""
        return bool(self._api_token)

    @property
    def token(self) -> Optional[str]:
        """Get the current API token."""
        return self._api_token

    @token.setter
    def token(self, value: str):
        """Set the API token."""
        self._api_token = value
