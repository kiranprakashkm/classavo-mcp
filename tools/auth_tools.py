"""Authentication tools for Classavo MCP Server."""

import logging
from typing import Any, Dict, Optional

from fastmcp import Context

from tools import mcp
from client import ClassavoClient
from auth import get_client, set_client

logger = logging.getLogger(__name__)


@mcp.tool(
    name="login",
    description="Login to Classavo with username (email) and password. "
    "Returns authentication token on success.",
    tags={"auth", "account"},
)
async def login(
    username: str,
    password: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Authenticate with Classavo API.

    Args:
        username: Email address or phone number
        password: Account password
        ctx: MCP context for logging

    Returns:
        Dict with token and success status
    """
    try:
        if ctx:
            await ctx.info(f"Logging in as {username}...")

        client = ClassavoClient()
        result = await client.login(username, password)

        # Store the authenticated client globally
        set_client(client)

        if ctx:
            await ctx.info("Login successful!")

        return {
            "status": "success",
            "message": f"Successfully logged in as {username}",
            "token": result.get("token"),
        }

    except Exception as e:
        error_msg = f"Login failed: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="logout",
    description="Logout from Classavo and invalidate the current session.",
    tags={"auth", "account"},
)
async def logout(ctx: Context = None) -> Dict[str, Any]:
    """
    Logout from Classavo API.

    Args:
        ctx: MCP context for logging

    Returns:
        Dict with success status
    """
    try:
        if ctx:
            await ctx.info("Logging out...")

        client = get_client()
        await client.logout()

        if ctx:
            await ctx.info("Logged out successfully")

        return {
            "status": "success",
            "message": "Successfully logged out",
        }

    except Exception as e:
        error_msg = f"Logout failed: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="get_my_profile",
    description="Get the current user's profile information including name, "
    "email, role (student/professor), and verification status.",
    tags={"auth", "account", "profile"},
)
async def get_my_profile(ctx: Context = None) -> Dict[str, Any]:
    """
    Get current user's profile.

    Args:
        ctx: MCP context for logging

    Returns:
        Dict with user profile data
    """
    try:
        if ctx:
            await ctx.info("Fetching profile...")

        client = get_client()
        result = await client.get("/api/me")

        user = result.get("user", result)
        role = "Professor" if user.get("role") == 2 else "Student"

        if ctx:
            await ctx.info(f"Profile loaded: {user.get('first_name')} ({role})")

        return {
            "status": "success",
            "user": {
                "identity": user.get("identity"),
                "email": user.get("email"),
                "first_name": user.get("first_name"),
                "last_name": user.get("last_name"),
                "role": role,
                "role_id": user.get("role"),
                "is_verified": user.get("is_verified"),
                "is_email_verified": user.get("is_email_verified"),
                "avatar_url": user.get("avatar_url"),
                "created_at": user.get("created_at"),
            },
            "flags": result.get("flags", {}),
            "milestones": result.get("milestones", {}),
        }

    except Exception as e:
        error_msg = f"Failed to get profile: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="get_notifications",
    description="Get the current user's notifications.",
    tags={"account", "notifications"},
)
async def get_notifications(ctx: Context = None) -> Dict[str, Any]:
    """
    Get user's notifications.

    Args:
        ctx: MCP context for logging

    Returns:
        Dict with notifications list
    """
    try:
        if ctx:
            await ctx.info("Fetching notifications...")

        client = get_client()
        result = await client.get("/api/me/notifications")

        notifications = result if isinstance(result, list) else result.get("notifications", [])
        unread_count = sum(1 for n in notifications if not n.get("is_seen", False))

        if ctx:
            await ctx.info(f"Found {len(notifications)} notifications ({unread_count} unread)")

        return {
            "status": "success",
            "total": len(notifications),
            "unread_count": unread_count,
            "notifications": notifications,
        }

    except Exception as e:
        error_msg = f"Failed to get notifications: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="mark_notification_seen",
    description="Mark a notification as seen/read.",
    tags={"account", "notifications"},
)
async def mark_notification_seen(
    notification_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Mark a notification as seen.

    Args:
        notification_id: The notification identity/ID
        ctx: MCP context for logging

    Returns:
        Dict with success status
    """
    try:
        if ctx:
            await ctx.info(f"Marking notification {notification_id} as seen...")

        client = get_client()
        await client.put(
            "/api/me/notifications",
            data={"identity": notification_id, "is_seen": True},
        )

        if ctx:
            await ctx.info("Notification marked as seen")

        return {
            "status": "success",
            "message": "Notification marked as seen",
        }

    except Exception as e:
        error_msg = f"Failed to mark notification: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)
