"""Discussion board tools for Classavo MCP Server."""

import logging
from typing import Any, Dict, List, Optional

from fastmcp import Context

from tools import mcp
from auth import get_client

logger = logging.getLogger(__name__)


@mcp.tool(
    name="list_discussions",
    description="List all discussion threads for a course.",
    tags={"discussions", "professor", "student"},
)
async def list_discussions(
    course_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    List all discussion threads for a course.

    Args:
        course_id: The course ID
        ctx: MCP context for logging

    Returns:
        Dict with list of discussion threads
    """
    try:
        if ctx:
            await ctx.info(f"Fetching discussions for course {course_id}...")

        client = get_client()
        result = await client.get("/api/discussions/", params={"course": course_id})

        discussions = result if isinstance(result, list) else result.get("results", [])

        if ctx:
            await ctx.info(f"Found {len(discussions)} discussions")

        return {
            "status": "success",
            "course_id": course_id,
            "count": len(discussions),
            "discussions": discussions,
        }

    except Exception as e:
        error_msg = f"Failed to list discussions: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="get_discussion",
    description="Get details of a specific discussion thread including comments.",
    tags={"discussions", "professor", "student"},
)
async def get_discussion(
    discussion_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get discussion thread details.

    Args:
        discussion_id: The discussion ID
        ctx: MCP context for logging

    Returns:
        Dict with discussion details and comments
    """
    try:
        if ctx:
            await ctx.info(f"Fetching discussion {discussion_id}...")

        client = get_client()
        result = await client.get(f"/api/discussions/{discussion_id}/")

        if ctx:
            await ctx.info("Discussion loaded successfully")

        return {
            "status": "success",
            "discussion": result,
        }

    except Exception as e:
        error_msg = f"Failed to get discussion: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="create_discussion",
    description="[PROFESSOR ONLY] Create a new discussion thread for a course.",
    tags={"discussions", "professor"},
)
async def create_discussion(
    course_id: str,
    title: str,
    content: str,
    chapter_id: str = None,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Create a new discussion thread.

    Args:
        course_id: The course ID
        title: Discussion title
        content: Initial post content
        chapter_id: Optional chapter ID to link discussion to
        ctx: MCP context for logging

    Returns:
        Dict with created discussion data
    """
    try:
        if ctx:
            await ctx.info(f"Creating discussion: {title}...")

        client = get_client()
        data = {
            "course": course_id,
            "title": title,
            "content": content,
        }
        if chapter_id:
            data["chapter"] = chapter_id

        result = await client.post("/api/discussions/", data=data)

        if ctx:
            await ctx.info("Discussion created successfully!")

        return {
            "status": "success",
            "message": "Discussion created",
            "discussion": result,
        }

    except Exception as e:
        error_msg = f"Failed to create discussion: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="post_comment",
    description="Post a comment/reply in a discussion thread.",
    tags={"discussions", "professor", "student"},
)
async def post_comment(
    discussion_id: str,
    content: str,
    parent_comment_id: str = None,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Post a comment in a discussion.

    Args:
        discussion_id: The discussion ID
        content: Comment text
        parent_comment_id: Optional parent comment ID for threaded replies
        ctx: MCP context for logging

    Returns:
        Dict with created comment data
    """
    try:
        if ctx:
            await ctx.info(f"Posting comment to discussion {discussion_id}...")

        client = get_client()
        data = {"content": content}
        if parent_comment_id:
            data["parent"] = parent_comment_id

        result = await client.post(
            f"/api/discussions/{discussion_id}/comments/",
            data=data,
        )

        if ctx:
            await ctx.info("Comment posted successfully!")

        return {
            "status": "success",
            "message": "Comment posted",
            "comment": result,
        }

    except Exception as e:
        error_msg = f"Failed to post comment: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="get_discussion_comments",
    description="Get all comments for a discussion thread.",
    tags={"discussions", "professor", "student"},
)
async def get_discussion_comments(
    discussion_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get all comments for a discussion.

    Args:
        discussion_id: The discussion ID
        ctx: MCP context for logging

    Returns:
        Dict with list of comments
    """
    try:
        if ctx:
            await ctx.info(f"Fetching comments for discussion {discussion_id}...")

        client = get_client()
        result = await client.get(f"/api/discussions/{discussion_id}/comments/")

        comments = result if isinstance(result, list) else result.get("comments", [])

        if ctx:
            await ctx.info(f"Found {len(comments)} comments")

        return {
            "status": "success",
            "discussion_id": discussion_id,
            "count": len(comments),
            "comments": comments,
        }

    except Exception as e:
        error_msg = f"Failed to get comments: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="pin_comment",
    description="[PROFESSOR ONLY] Pin an important comment in a discussion.",
    tags={"discussions", "professor"},
)
async def pin_comment(
    discussion_id: str,
    comment_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Pin a comment in a discussion.

    Args:
        discussion_id: The discussion ID
        comment_id: The comment ID to pin
        ctx: MCP context for logging

    Returns:
        Dict with pin status
    """
    try:
        if ctx:
            await ctx.info(f"Pinning comment {comment_id}...")

        client = get_client()
        result = await client.post(
            f"/api/discussions/{discussion_id}/comments/{comment_id}/pin/",
        )

        if ctx:
            await ctx.info("Comment pinned successfully!")

        return {
            "status": "success",
            "message": "Comment pinned",
            "discussion_id": discussion_id,
            "comment_id": comment_id,
            "result": result,
        }

    except Exception as e:
        error_msg = f"Failed to pin comment: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="unpin_comment",
    description="[PROFESSOR ONLY] Unpin a previously pinned comment.",
    tags={"discussions", "professor"},
)
async def unpin_comment(
    discussion_id: str,
    comment_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Unpin a comment in a discussion.

    Args:
        discussion_id: The discussion ID
        comment_id: The comment ID to unpin
        ctx: MCP context for logging

    Returns:
        Dict with unpin status
    """
    try:
        if ctx:
            await ctx.info(f"Unpinning comment {comment_id}...")

        client = get_client()
        result = await client.post(
            f"/api/discussions/{discussion_id}/comments/{comment_id}/unpin/",
        )

        if ctx:
            await ctx.info("Comment unpinned successfully!")

        return {
            "status": "success",
            "message": "Comment unpinned",
            "discussion_id": discussion_id,
            "comment_id": comment_id,
            "result": result,
        }

    except Exception as e:
        error_msg = f"Failed to unpin comment: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="delete_discussion",
    description="[PROFESSOR ONLY] Delete a discussion thread.",
    tags={"discussions", "professor"},
)
async def delete_discussion(
    discussion_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Delete a discussion thread.

    Args:
        discussion_id: The discussion ID
        ctx: MCP context for logging

    Returns:
        Dict with deletion status
    """
    try:
        if ctx:
            await ctx.info(f"Deleting discussion {discussion_id}...")

        client = get_client()
        await client.delete(f"/api/discussions/{discussion_id}/")

        if ctx:
            await ctx.info("Discussion deleted successfully!")

        return {
            "status": "success",
            "message": "Discussion deleted",
            "discussion_id": discussion_id,
        }

    except Exception as e:
        error_msg = f"Failed to delete discussion: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="delete_comment",
    description="Delete a comment. Users can delete their own comments, professors can delete any.",
    tags={"discussions", "professor", "student"},
)
async def delete_comment(
    discussion_id: str,
    comment_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Delete a comment.

    Args:
        discussion_id: The discussion ID
        comment_id: The comment ID
        ctx: MCP context for logging

    Returns:
        Dict with deletion status
    """
    try:
        if ctx:
            await ctx.info(f"Deleting comment {comment_id}...")

        client = get_client()
        await client.delete(f"/api/discussions/{discussion_id}/comments/{comment_id}/")

        if ctx:
            await ctx.info("Comment deleted successfully!")

        return {
            "status": "success",
            "message": "Comment deleted",
            "discussion_id": discussion_id,
            "comment_id": comment_id,
        }

    except Exception as e:
        error_msg = f"Failed to delete comment: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)
