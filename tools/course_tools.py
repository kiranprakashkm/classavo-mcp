"""Course management tools for Classavo MCP Server."""

import logging
from typing import Any, Dict, List, Optional

from fastmcp import Context

from tools import mcp
from auth import get_client

logger = logging.getLogger(__name__)


@mcp.tool(
    name="list_courses",
    description="List all courses for the current user. "
    "Professors see courses they teach, students see enrolled courses.",
    tags={"courses", "professor", "student"},
)
async def list_courses(ctx: Context = None) -> Dict[str, Any]:
    """
    List all courses for the current user.

    Args:
        ctx: MCP context for logging

    Returns:
        Dict with list of courses
    """
    try:
        if ctx:
            await ctx.info("Fetching courses...")

        client = get_client()
        result = await client.get("/api/v2/courses/")

        courses = result if isinstance(result, list) else result.get("results", result.get("courses", []))

        if ctx:
            await ctx.info(f"Found {len(courses)} courses")

        return {
            "status": "success",
            "count": len(courses),
            "courses": courses,
        }

    except Exception as e:
        error_msg = f"Failed to list courses: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="get_course",
    description="Get detailed information about a specific course.",
    tags={"courses", "professor", "student"},
)
async def get_course(
    course_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get course details.

    Args:
        course_id: The course ID
        ctx: MCP context for logging

    Returns:
        Dict with course details
    """
    try:
        if ctx:
            await ctx.info(f"Fetching course {course_id}...")

        client = get_client()
        result = await client.get(f"/api/courses/{course_id}/")

        if ctx:
            await ctx.info(f"Found course: {result.get('name', 'Unknown')}")

        return {
            "status": "success",
            "course": result,
        }

    except Exception as e:
        error_msg = f"Failed to get course: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="create_course",
    description="[PROFESSOR ONLY] Create a new course.",
    tags={"courses", "professor"},
)
async def create_course(
    name: str,
    description: str = "",
    course_number: str = "",
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Create a new course.

    Args:
        name: Course name (e.g., "Chemistry 101")
        description: Course description
        course_number: Course number/code
        ctx: MCP context for logging

    Returns:
        Dict with created course data
    """
    try:
        if ctx:
            await ctx.info(f"Creating course: {name}...")

        client = get_client()
        result = await client.post(
            "/api/v2/courses/",
            data={
                "name": name,
                "description": description,
                "course_number": course_number,
            },
        )

        if ctx:
            await ctx.info(f"Course created successfully!")

        return {
            "status": "success",
            "message": f"Course '{name}' created",
            "course": result,
        }

    except Exception as e:
        error_msg = f"Failed to create course: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="get_course_roster",
    description="[PROFESSOR ONLY] Get the list of students enrolled in a course.",
    tags={"courses", "professor", "roster"},
)
async def get_course_roster(
    course_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get course roster (enrolled students).

    Args:
        course_id: The course ID
        ctx: MCP context for logging

    Returns:
        Dict with list of students
    """
    try:
        if ctx:
            await ctx.info(f"Fetching roster for course {course_id}...")

        client = get_client()
        result = await client.get(f"/api/courses/{course_id}/students/")

        students = result if isinstance(result, list) else result.get("students", [])

        if ctx:
            await ctx.info(f"Found {len(students)} students")

        return {
            "status": "success",
            "course_id": course_id,
            "count": len(students),
            "students": students,
        }

    except Exception as e:
        error_msg = f"Failed to get roster: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="get_course_instructors",
    description="Get the list of instructors for a course.",
    tags={"courses", "professor"},
)
async def get_course_instructors(
    course_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get course instructors.

    Args:
        course_id: The course ID
        ctx: MCP context for logging

    Returns:
        Dict with list of instructors
    """
    try:
        if ctx:
            await ctx.info(f"Fetching instructors for course {course_id}...")

        client = get_client()
        result = await client.get(f"/api/courses/{course_id}/instructors/")

        instructors = result if isinstance(result, list) else result.get("instructors", [])

        if ctx:
            await ctx.info(f"Found {len(instructors)} instructors")

        return {
            "status": "success",
            "course_id": course_id,
            "count": len(instructors),
            "instructors": instructors,
        }

    except Exception as e:
        error_msg = f"Failed to get instructors: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="invite_students",
    description="[PROFESSOR ONLY] Invite students to a course by email.",
    tags={"courses", "professor", "invitations"},
)
async def invite_students(
    course_id: str,
    emails: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Invite students to a course.

    Args:
        course_id: The course ID
        emails: Comma-separated list of student email addresses
        ctx: MCP context for logging

    Returns:
        Dict with invitation status
    """
    try:
        email_list = [e.strip() for e in emails.split(",") if e.strip()]

        if ctx:
            await ctx.info(f"Inviting {len(email_list)} students to course {course_id}...")

        client = get_client()
        result = await client.post(
            f"/api/v2/courses/{course_id}/invitations/",
            data={"emails": email_list, "role": "student"},
        )

        if ctx:
            await ctx.info(f"Invitations sent successfully!")

        return {
            "status": "success",
            "message": f"Invited {len(email_list)} students",
            "course_id": course_id,
            "result": result,
        }

    except Exception as e:
        error_msg = f"Failed to invite students: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="join_course",
    description="[STUDENT ONLY] Join a course using an invite code.",
    tags={"courses", "student"},
)
async def join_course(
    invite_code: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Join a course using invite code.

    Args:
        invite_code: The course invite code
        ctx: MCP context for logging

    Returns:
        Dict with join status
    """
    try:
        if ctx:
            await ctx.info(f"Joining course with code: {invite_code}...")

        client = get_client()
        result = await client.post(
            "/api/courses/join/",
            data={"invite_code": invite_code},
        )

        if ctx:
            await ctx.info("Successfully joined the course!")

        return {
            "status": "success",
            "message": "Successfully joined the course",
            "result": result,
        }

    except Exception as e:
        error_msg = f"Failed to join course: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="get_course_analytics",
    description="[PROFESSOR ONLY] Get analytics and insights for a course.",
    tags={"courses", "professor", "analytics"},
)
async def get_course_analytics(
    course_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get course analytics/insights.

    Args:
        course_id: The course ID
        ctx: MCP context for logging

    Returns:
        Dict with course analytics
    """
    try:
        if ctx:
            await ctx.info(f"Fetching analytics for course {course_id}...")

        client = get_client()
        result = await client.get(f"/api/v2/insights/", params={"course": course_id})

        if ctx:
            await ctx.info("Analytics loaded successfully")

        return {
            "status": "success",
            "course_id": course_id,
            "insights": result,
        }

    except Exception as e:
        error_msg = f"Failed to get analytics: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)
