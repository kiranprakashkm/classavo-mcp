"""Authentication utilities for Classavo MCP Server."""

import logging
from typing import Optional

from config import config
from client import ClassavoClient

logger = logging.getLogger(__name__)


# Global client instance for session persistence
_client: Optional[ClassavoClient] = None


def get_client() -> ClassavoClient:
    """Get or create the global Classavo client instance."""
    global _client
    if _client is None:
        _client = ClassavoClient()
    return _client


def set_client(client: ClassavoClient) -> None:
    """Set the global client instance (useful after login)."""
    global _client
    _client = client


async def auto_login() -> Optional[ClassavoClient]:
    """
    Automatically login using configured credentials.

    Returns:
        ClassavoClient if login successful, None otherwise
    """
    client = get_client()

    # If already authenticated with token, return client
    if client.is_authenticated:
        logger.info("Using existing authentication token")
        return client

    # Try to login with credentials
    if config.has_credentials:
        try:
            await client.login(config.username, config.password)
            logger.info(f"Auto-logged in as {config.username}")
            return client
        except Exception as e:
            logger.error(f"Auto-login failed: {str(e)}")
            return None

    # No auth configured
    logger.warning("No authentication configured. Set CLASSAVO_API_TOKEN or credentials.")
    return None


async def get_current_user_role(client: ClassavoClient) -> int:
    """
    Get the current user's role.

    Returns:
        1 = Student, 2 = Professor
    """
    try:
        user_data = await client.get_current_user()
        user = user_data.get("user", user_data)
        return user.get("role", 1)
    except Exception as e:
        logger.error(f"Failed to get user role: {str(e)}")
        return 1  # Default to student (most restrictive)


def is_professor(role: int) -> bool:
    """Check if role is professor."""
    return role == 2


def is_student(role: int) -> bool:
    """Check if role is student."""
    return role == 1
