"""Live polling tools for Classavo MCP Server."""

import logging
from typing import Any, Dict, List, Optional

from fastmcp import Context

from tools import mcp
from auth import get_client

logger = logging.getLogger(__name__)


@mcp.tool(
    name="list_polls",
    description="[PROFESSOR ONLY] List all polls for a course.",
    tags={"polling", "professor"},
)
async def list_polls(
    course_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    List all polls for a course.

    Args:
        course_id: The course ID
        ctx: MCP context for logging

    Returns:
        Dict with list of polls
    """
    try:
        if ctx:
            await ctx.info(f"Fetching polls for course {course_id}...")

        client = get_client()
        result = await client.get("/api/v2/polling/", params={"course": course_id})

        polls = result if isinstance(result, list) else result.get("results", [])

        if ctx:
            await ctx.info(f"Found {len(polls)} polls")

        return {
            "status": "success",
            "course_id": course_id,
            "count": len(polls),
            "polls": polls,
        }

    except Exception as e:
        error_msg = f"Failed to list polls: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="create_poll",
    description="[PROFESSOR ONLY] Create a new poll for a course.",
    tags={"polling", "professor"},
)
async def create_poll(
    course_id: str,
    question: str,
    options: str,
    allow_multiple: bool = False,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Create a new poll.

    Args:
        course_id: The course ID
        question: The poll question
        options: Comma-separated answer options (e.g., "A,B,C,D")
        allow_multiple: Allow multiple answers (default False)
        ctx: MCP context for logging

    Returns:
        Dict with created poll data
    """
    try:
        if ctx:
            await ctx.info(f"Creating poll: {question[:50]}...")

        client = get_client()

        # Parse options
        option_list = [o.strip() for o in options.split(",") if o.strip()]

        data = {
            "course": course_id,
            "question": question,
            "options": [{"text": opt} for opt in option_list],
            "allow_multiple": allow_multiple,
        }

        result = await client.post("/api/v2/polling/", data=data)

        if ctx:
            await ctx.info("Poll created successfully!")

        return {
            "status": "success",
            "message": "Poll created",
            "poll": result,
        }

    except Exception as e:
        error_msg = f"Failed to create poll: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="start_poll",
    description="[PROFESSOR ONLY] Start/launch a poll for students to vote on.",
    tags={"polling", "professor"},
)
async def start_poll(
    poll_id: str,
    duration_seconds: int = 60,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Start a poll.

    Args:
        poll_id: The poll ID
        duration_seconds: How long the poll stays open (default 60 seconds)
        ctx: MCP context for logging

    Returns:
        Dict with poll status
    """
    try:
        if ctx:
            await ctx.info(f"Starting poll {poll_id}...")

        client = get_client()
        result = await client.post(
            f"/api/v2/polling/{poll_id}/start/",
            data={"duration": duration_seconds},
        )

        if ctx:
            await ctx.info(f"Poll started! Open for {duration_seconds} seconds")

        return {
            "status": "success",
            "message": f"Poll started for {duration_seconds} seconds",
            "poll_id": poll_id,
            "result": result,
        }

    except Exception as e:
        error_msg = f"Failed to start poll: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="end_poll",
    description="[PROFESSOR ONLY] End an active poll.",
    tags={"polling", "professor"},
)
async def end_poll(
    poll_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    End a poll.

    Args:
        poll_id: The poll ID
        ctx: MCP context for logging

    Returns:
        Dict with poll results
    """
    try:
        if ctx:
            await ctx.info(f"Ending poll {poll_id}...")

        client = get_client()
        result = await client.post(f"/api/v2/polling/{poll_id}/end/")

        if ctx:
            await ctx.info("Poll ended")

        return {
            "status": "success",
            "message": "Poll ended",
            "poll_id": poll_id,
            "result": result,
        }

    except Exception as e:
        error_msg = f"Failed to end poll: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="get_poll_results",
    description="[PROFESSOR ONLY] Get results for a poll.",
    tags={"polling", "professor"},
)
async def get_poll_results(
    poll_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get poll results.

    Args:
        poll_id: The poll ID
        ctx: MCP context for logging

    Returns:
        Dict with poll results and vote counts
    """
    try:
        if ctx:
            await ctx.info(f"Fetching results for poll {poll_id}...")

        client = get_client()
        result = await client.get(f"/api/v2/polling/{poll_id}/results/")

        if ctx:
            await ctx.info("Poll results loaded")

        return {
            "status": "success",
            "poll_id": poll_id,
            "results": result,
        }

    except Exception as e:
        error_msg = f"Failed to get poll results: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="delete_poll",
    description="[PROFESSOR ONLY] Delete a poll.",
    tags={"polling", "professor"},
)
async def delete_poll(
    poll_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Delete a poll.

    Args:
        poll_id: The poll ID
        ctx: MCP context for logging

    Returns:
        Dict with success status
    """
    try:
        if ctx:
            await ctx.info(f"Deleting poll {poll_id}...")

        client = get_client()
        await client.delete(f"/api/v2/polling/{poll_id}/")

        if ctx:
            await ctx.info("Poll deleted successfully")

        return {
            "status": "success",
            "message": "Poll deleted",
            "poll_id": poll_id,
        }

    except Exception as e:
        error_msg = f"Failed to delete poll: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="vote_in_poll",
    description="[STUDENT] Cast your vote in an active poll.",
    tags={"polling", "student"},
)
async def vote_in_poll(
    poll_id: str,
    option_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Vote in a poll.

    Args:
        poll_id: The poll ID
        option_id: The option ID to vote for
        ctx: MCP context for logging

    Returns:
        Dict with vote confirmation
    """
    try:
        if ctx:
            await ctx.info(f"Voting in poll {poll_id}...")

        client = get_client()
        result = await client.post(
            f"/api/v2/polling/{poll_id}/vote/",
            data={"option": option_id},
        )

        if ctx:
            await ctx.info("Vote recorded!")

        return {
            "status": "success",
            "message": "Vote recorded",
            "poll_id": poll_id,
            "result": result,
        }

    except Exception as e:
        error_msg = f"Failed to vote: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)
