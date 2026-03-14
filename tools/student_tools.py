"""Student-specific tools for Classavo MCP Server.

PRIVACY CONTROLS:
- Students can ONLY view their OWN grades, submissions, and attendance
- Tools do NOT accept student_id parameters - always uses logged-in user
- API endpoints return only the authenticated student's data
"""

import logging
from typing import Any, Dict, List, Optional

from fastmcp import Context

from tools import mcp
from auth import get_client

logger = logging.getLogger(__name__)


@mcp.tool(
    name="view_my_grades",
    description="[STUDENT] View YOUR grades in a course. "
    "Only shows your own grades - you cannot see other students' grades.",
    tags={"student", "grades", "privacy"},
)
async def view_my_grades(
    course_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    View the logged-in student's grades for a course.

    PRIVACY: This tool only returns the authenticated student's grades.
    No student_id parameter is accepted to prevent viewing other students' data.

    Args:
        course_id: The course ID
        ctx: MCP context for logging

    Returns:
        Dict with the student's grades
    """
    try:
        if ctx:
            await ctx.info(f"Fetching your grades for course {course_id}...")

        client = get_client()
        # API endpoint returns ONLY the logged-in student's grades
        result = await client.get(
            "/api/v2/gradebook/student/",
            params={"course": course_id},
        )

        if ctx:
            await ctx.info("Your grades loaded successfully")

        return {
            "status": "success",
            "course_id": course_id,
            "grades": result,
        }

    except Exception as e:
        error_msg = f"Failed to fetch grades: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="view_my_submissions",
    description="[STUDENT] View YOUR submissions for an assignment. "
    "Only shows your own submissions.",
    tags={"student", "submissions", "privacy"},
)
async def view_my_submissions(
    assignment_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    View the logged-in student's submissions for an assignment.

    PRIVACY: Returns only the authenticated student's submissions.

    Args:
        assignment_id: The assignment ID
        ctx: MCP context for logging

    Returns:
        Dict with the student's submissions
    """
    try:
        if ctx:
            await ctx.info(f"Fetching your submissions for assignment {assignment_id}...")

        client = get_client()
        # student=me tells the API to return only logged-in user's submissions
        result = await client.get(
            "/api/v2/submissions/",
            params={"assignment": assignment_id, "student": "me"},
        )

        submissions = result if isinstance(result, list) else result.get("results", [])

        if ctx:
            await ctx.info(f"Found {len(submissions)} submission(s)")

        return {
            "status": "success",
            "assignment_id": assignment_id,
            "count": len(submissions),
            "submissions": submissions,
        }

    except Exception as e:
        error_msg = f"Failed to fetch submissions: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="submit_assignment",
    description="[STUDENT] Submit your work for an assignment.",
    tags={"student", "submissions"},
)
async def submit_assignment(
    assignment_id: str,
    content: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Submit an assignment.

    Args:
        assignment_id: The assignment ID
        content: Submission content (text/answers)
        ctx: MCP context for logging

    Returns:
        Dict with submission confirmation
    """
    try:
        if ctx:
            await ctx.info(f"Submitting assignment {assignment_id}...")

        client = get_client()
        result = await client.post(
            "/api/v2/submissions/",
            data={
                "assignment": assignment_id,
                "content": content,
            },
        )

        if ctx:
            await ctx.info("Assignment submitted successfully!")

        return {
            "status": "success",
            "message": "Assignment submitted",
            "submission": result,
        }

    except Exception as e:
        error_msg = f"Failed to submit assignment: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="check_in_attendance",
    description="[STUDENT] Mark yourself present using an attendance code.",
    tags={"student", "attendance"},
)
async def check_in_attendance(
    code: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Check in to an attendance session using a code.

    Args:
        code: The attendance code provided by the professor
        ctx: MCP context for logging

    Returns:
        Dict with check-in confirmation
    """
    try:
        if ctx:
            await ctx.info(f"Checking in with code: {code}...")

        client = get_client()
        result = await client.post(
            "/api/v2/attendance/checkin/",
            data={"code": code},
        )

        if ctx:
            await ctx.info("Check-in successful! You're marked as present.")

        return {
            "status": "success",
            "message": "Attendance recorded",
            "result": result,
        }

    except Exception as e:
        error_msg = f"Failed to check in: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="view_my_attendance",
    description="[STUDENT] View YOUR attendance record for a course. "
    "Only shows your own attendance history.",
    tags={"student", "attendance", "privacy"},
)
async def view_my_attendance(
    course_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    View the logged-in student's attendance for a course.

    PRIVACY: Returns only the authenticated student's attendance.

    Args:
        course_id: The course ID
        ctx: MCP context for logging

    Returns:
        Dict with the student's attendance record
    """
    try:
        if ctx:
            await ctx.info(f"Fetching your attendance for course {course_id}...")

        client = get_client()
        result = await client.get(
            "/api/v2/attendance/student/",
            params={"course": course_id},
        )

        if ctx:
            await ctx.info("Your attendance record loaded")

        return {
            "status": "success",
            "course_id": course_id,
            "attendance": result,
        }

    except Exception as e:
        error_msg = f"Failed to fetch attendance: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="view_upcoming_deadlines",
    description="[STUDENT] View your upcoming assignment deadlines and due dates.",
    tags={"student", "dashboard"},
)
async def view_upcoming_deadlines(
    course_id: str = None,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    View upcoming deadlines.

    Args:
        course_id: Optional course ID to filter by
        ctx: MCP context for logging

    Returns:
        Dict with upcoming deadlines
    """
    try:
        if ctx:
            await ctx.info("Fetching your upcoming deadlines...")

        client = get_client()
        params = {}
        if course_id:
            params["course"] = course_id

        result = await client.get("/api/v2/dashboard/deadlines/", params=params)

        deadlines = result if isinstance(result, list) else result.get("deadlines", [])

        if ctx:
            await ctx.info(f"Found {len(deadlines)} upcoming deadline(s)")

        return {
            "status": "success",
            "count": len(deadlines),
            "deadlines": deadlines,
        }

    except Exception as e:
        error_msg = f"Failed to fetch deadlines: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="view_chapter_content",
    description="[STUDENT] View a chapter/textbook content.",
    tags={"student", "content"},
)
async def view_chapter_content(
    chapter_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    View chapter content.

    Args:
        chapter_id: The chapter ID
        ctx: MCP context for logging

    Returns:
        Dict with chapter content
    """
    try:
        if ctx:
            await ctx.info(f"Fetching chapter {chapter_id} content...")

        client = get_client()
        result = await client.get(f"/api/file/{chapter_id}/")

        if ctx:
            await ctx.info("Chapter content loaded")

        return {
            "status": "success",
            "chapter": result,
        }

    except Exception as e:
        error_msg = f"Failed to fetch chapter: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="get_active_polls",
    description="[STUDENT] Get active polls you can vote on.",
    tags={"student", "polling"},
)
async def get_active_polls(
    course_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get active polls for a course.

    Args:
        course_id: The course ID
        ctx: MCP context for logging

    Returns:
        Dict with active polls
    """
    try:
        if ctx:
            await ctx.info(f"Fetching active polls for course {course_id}...")

        client = get_client()
        result = await client.get(
            "/api/v2/polling/active/",
            params={"course": course_id},
        )

        polls = result if isinstance(result, list) else result.get("polls", [])

        if ctx:
            await ctx.info(f"Found {len(polls)} active poll(s)")

        return {
            "status": "success",
            "course_id": course_id,
            "count": len(polls),
            "polls": polls,
        }

    except Exception as e:
        error_msg = f"Failed to fetch polls: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="global_search",
    description="Search across your courses for content, discussions, and more.",
    tags={"student", "professor", "search"},
)
async def global_search(
    query: str,
    course_id: str = None,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Search across courses.

    Args:
        query: Search query
        course_id: Optional course ID to limit search
        ctx: MCP context for logging

    Returns:
        Dict with search results
    """
    try:
        if ctx:
            await ctx.info(f"Searching for: {query}...")

        client = get_client()
        params = {"q": query}
        if course_id:
            params["course"] = course_id

        result = await client.get("/api/v2/search/", params=params)

        if ctx:
            await ctx.info("Search completed")

        return {
            "status": "success",
            "query": query,
            "results": result,
        }

    except Exception as e:
        error_msg = f"Search failed: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)
