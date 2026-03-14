"""Grading and submission tools for Classavo MCP Server."""

import logging
from typing import Any, Dict, Optional

from fastmcp import Context

from tools import mcp
from auth import get_client

logger = logging.getLogger(__name__)


@mcp.tool(
    name="list_submissions",
    description="[PROFESSOR ONLY] List all submissions for a question.",
    tags={"grading", "professor", "submissions"},
)
async def list_submissions(
    question_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    List submissions for a question.

    Args:
        question_id: The question ID (UUID)
        ctx: MCP context for logging

    Returns:
        Dict with list of submissions
    """
    try:
        if ctx:
            await ctx.info(f"Fetching submissions for question {question_id}...")

        client = get_client()
        result = await client.get(f"/api/questions/{question_id}/submissions")

        submissions = result if isinstance(result, list) else result.get("results", [])

        if ctx:
            await ctx.info(f"Found {len(submissions)} submissions")

        return {
            "status": "success",
            "question_id": question_id,
            "count": len(submissions),
            "submissions": submissions,
        }

    except Exception as e:
        error_msg = f"Failed to list submissions: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="get_submission",
    description="[PROFESSOR ONLY] Get detailed information about a specific submission.",
    tags={"grading", "professor", "submissions"},
)
async def get_submission(
    submission_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get submission details.

    Args:
        submission_id: The submission ID
        ctx: MCP context for logging

    Returns:
        Dict with submission details
    """
    try:
        if ctx:
            await ctx.info(f"Fetching submission {submission_id}...")

        client = get_client()
        result = await client.get(f"/api/v2/submissions/{submission_id}/review/")

        if ctx:
            await ctx.info("Submission loaded successfully")

        return {
            "status": "success",
            "submission": result,
        }

    except Exception as e:
        error_msg = f"Failed to get submission: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="grade_submission",
    description="[PROFESSOR ONLY] Grade a student's submission.",
    tags={"grading", "professor"},
)
async def grade_submission(
    submission_id: str,
    score: float,
    feedback: str = None,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Grade a submission.

    Args:
        submission_id: The submission ID
        score: The score/grade to assign
        feedback: Optional feedback for the student
        ctx: MCP context for logging

    Returns:
        Dict with updated submission
    """
    try:
        if ctx:
            await ctx.info(f"Grading submission {submission_id} with score {score}...")

        client = get_client()
        data = {"score": score}
        if feedback:
            data["feedback"] = feedback

        result = await client.patch(f"/api/v2/submissions/{submission_id}/grade/", data=data)

        if ctx:
            await ctx.info(f"Submission graded: {score} points")

        return {
            "status": "success",
            "message": f"Submission graded with score {score}",
            "submission_id": submission_id,
            "result": result,
        }

    except Exception as e:
        error_msg = f"Failed to grade submission: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="get_gradebook",
    description="[PROFESSOR ONLY] Get the full gradebook for a course showing all student grades.",
    tags={"grading", "professor", "gradebook"},
)
async def get_gradebook(
    course_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get course gradebook.

    Args:
        course_id: The course ID
        ctx: MCP context for logging

    Returns:
        Dict with gradebook data
    """
    try:
        if ctx:
            await ctx.info(f"Fetching gradebook for course {course_id}...")

        client = get_client()

        # Verify user is a professor
        user = await client.get_current_user()
        user_data = user.get("user", user)
        if user_data.get("role") != 2:
            raise PermissionError("Only professors can view the full gradebook")

        result = await client.get(f"/api/courses/{course_id}/gradebook/all")

        if ctx:
            await ctx.info("Gradebook loaded successfully")

        return {
            "status": "success",
            "course_id": course_id,
            "gradebook": result,
        }

    except PermissionError as e:
        error_msg = str(e)
        if ctx:
            await ctx.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Failed to get gradebook: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="update_feedback",
    description="[PROFESSOR ONLY] Update or add feedback for a student's submission.",
    tags={"grading", "professor", "feedback"},
)
async def update_feedback(
    submission_id: str,
    feedback: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Update feedback for a submission.

    Args:
        submission_id: The submission ID
        feedback: The feedback text
        ctx: MCP context for logging

    Returns:
        Dict with success status
    """
    try:
        if ctx:
            await ctx.info(f"Updating feedback for submission {submission_id}...")

        client = get_client()
        result = await client.patch(
            f"/api/v2/submissions/{submission_id}/feedback/",
            data={"feedback": feedback},
        )

        if ctx:
            await ctx.info("Feedback updated successfully")

        return {
            "status": "success",
            "message": "Feedback updated",
            "submission_id": submission_id,
            "result": result,
        }

    except Exception as e:
        error_msg = f"Failed to update feedback: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="export_gradebook",
    description="[PROFESSOR ONLY] Export gradebook to LMS format (Canvas, Blackboard, BrightSpace).",
    tags={"grading", "professor", "export", "lms"},
)
async def export_gradebook(
    course_id: str,
    format: str = "canvas",
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Export gradebook to LMS format.

    Args:
        course_id: The course ID
        format: Export format (canvas, blackboard, brightspace, classavo)
        ctx: MCP context for logging

    Returns:
        Dict with export data/URL
    """
    try:
        if ctx:
            await ctx.info(f"Exporting gradebook for course {course_id} to {format}...")

        client = get_client()

        # Map format to endpoint
        format_map = {
            "canvas": "canvas",
            "blackboard": "blackboard",
            "brightspace": "brightspace",
            "classavo": "classavo",
        }
        export_format = format_map.get(format.lower(), "classavo")

        result = await client.post(
            f"/api/v2/gradebook/course/{course_id}/export/{export_format}",
        )

        if ctx:
            await ctx.info(f"Gradebook exported to {format} format")

        return {
            "status": "success",
            "format": format,
            "course_id": course_id,
            "export_data": result,
        }

    except Exception as e:
        error_msg = f"Failed to export gradebook: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="get_submission_analysis",
    description="[PROFESSOR ONLY] Get analytics/statistics for submissions on an assignment.",
    tags={"grading", "professor", "analytics"},
)
async def get_submission_analysis(
    assignment_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get submission analytics for an assignment.

    Args:
        assignment_id: The assignment ID
        ctx: MCP context for logging

    Returns:
        Dict with submission statistics
    """
    try:
        if ctx:
            await ctx.info(f"Fetching submission analysis for assignment {assignment_id}...")

        client = get_client()
        result = await client.get(f"/api/v2/submissions/{assignment_id}/analysis/")

        if ctx:
            await ctx.info("Analysis loaded successfully")

        return {
            "status": "success",
            "assignment_id": assignment_id,
            "analysis": result,
        }

    except Exception as e:
        error_msg = f"Failed to get analysis: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)
