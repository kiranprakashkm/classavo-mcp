"""Attendance tracking tools for Classavo MCP Server."""

import logging
from typing import Any, Dict, Optional

from fastmcp import Context

from tools import mcp
from auth import get_client

logger = logging.getLogger(__name__)


@mcp.tool(
    name="start_attendance_session",
    description="[PROFESSOR ONLY] Start an attendance session for a class. "
    "Generates a code students can use to check in.",
    tags={"attendance", "professor"},
)
async def start_attendance_session(
    course_id: str,
    duration_minutes: int = 15,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Start an attendance session.

    Args:
        course_id: The course ID
        duration_minutes: How long the session stays active (default 15 min)
        ctx: MCP context for logging

    Returns:
        Dict with session details and attendance code
    """
    try:
        if ctx:
            await ctx.info(f"Starting attendance session for course {course_id}...")

        client = get_client()
        # Get today's date in ISO format
        from datetime import date
        today = date.today().isoformat()

        result = await client.post(
            "/api/v2/attendance/sessions/start/",
            data={
                "course_public_id": course_id,
                "attendance_date": today,
            },
        )

        code = result.get("code", result.get("attendance_code", "N/A"))

        if ctx:
            await ctx.info(f"Attendance session started! Code: {code}")

        return {
            "status": "success",
            "message": f"Attendance session started",
            "course_id": course_id,
            "attendance_code": code,
            "duration_minutes": duration_minutes,
            "session": result,
        }

    except Exception as e:
        error_msg = f"Failed to start attendance: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="end_attendance_session",
    description="[PROFESSOR ONLY] End an active attendance session.",
    tags={"attendance", "professor"},
)
async def end_attendance_session(
    course_id: str,
    session_code: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    End an attendance session.

    Args:
        course_id: The course public ID
        session_code: The attendance session code (e.g., "12345")
        ctx: MCP context for logging

    Returns:
        Dict with session summary
    """
    try:
        if ctx:
            await ctx.info(f"Ending attendance session {session_code}...")

        client = get_client()
        result = await client.post(
            "/api/v2/attendance/sessions/end/",
            data={"code": session_code, "course_public_id": course_id},
        )

        if ctx:
            await ctx.info("Attendance session ended")

        return {
            "status": "success",
            "message": "Attendance session ended",
            "session_code": session_code,
            "result": result,
        }

    except Exception as e:
        error_msg = f"Failed to end session: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="get_active_sessions",
    description="[PROFESSOR ONLY] Get active attendance sessions for a course.",
    tags={"attendance", "professor"},
)
async def get_active_sessions(
    course_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get active attendance sessions.

    Args:
        course_id: The course ID
        ctx: MCP context for logging

    Returns:
        Dict with active sessions
    """
    try:
        if ctx:
            await ctx.info(f"Fetching active sessions for course {course_id}...")

        client = get_client()
        result = await client.get(
            f"/api/v2/attendance/sessions/active/courses/{course_id}/",
        )

        sessions = result if isinstance(result, list) else result.get("sessions", [])

        if ctx:
            await ctx.info(f"Found {len(sessions)} active session(s)")

        return {
            "status": "success",
            "course_id": course_id,
            "count": len(sessions),
            "sessions": sessions,
        }

    except Exception as e:
        error_msg = f"Failed to get sessions: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="get_attendance_report",
    description="[PROFESSOR ONLY] Get attendance report for a course.",
    tags={"attendance", "professor", "reports"},
)
async def get_attendance_report(
    course_id: str,
    start_date: str = None,
    end_date: str = None,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get attendance report.

    Args:
        course_id: The course ID
        start_date: Filter from date (ISO format)
        end_date: Filter to date (ISO format)
        ctx: MCP context for logging

    Returns:
        Dict with attendance report
    """
    try:
        if ctx:
            await ctx.info(f"Fetching attendance report for course {course_id}...")

        client = get_client()
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        result = await client.get(f"/api/v2/attendance/report/{course_id}/", params=params if params else None)

        if ctx:
            await ctx.info("Attendance report loaded")

        return {
            "status": "success",
            "course_id": course_id,
            "report": result,
        }

    except Exception as e:
        error_msg = f"Failed to get report: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="mark_student_attendance",
    description="[PROFESSOR ONLY] Manually mark a student's attendance status.",
    tags={"attendance", "professor"},
)
async def mark_student_attendance(
    session_id: str,
    student_id: str,
    status: str = "present",
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Mark student attendance.

    Args:
        session_id: The attendance session ID
        student_id: The student's ID
        status: Attendance status (present, absent, late, excused)
        ctx: MCP context for logging

    Returns:
        Dict with update result
    """
    try:
        if ctx:
            await ctx.info(f"Marking student {student_id} as {status}...")

        client = get_client()

        # Map status to API values
        status_map = {
            "present": "present",
            "absent": "absent",
            "late": "late",
            "excused": "excused",
        }
        api_status = status_map.get(status.lower(), "present")

        result = await client.patch(
            f"/api/v2/attendance/sessions/{session_id}/students/{student_id}/",
            data={"status": api_status},
        )

        if ctx:
            await ctx.info(f"Student marked as {status}")

        return {
            "status": "success",
            "message": f"Student marked as {status}",
            "session_id": session_id,
            "student_id": student_id,
            "attendance_status": api_status,
            "result": result,
        }

    except Exception as e:
        error_msg = f"Failed to mark attendance: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="excuse_student",
    description="[PROFESSOR ONLY] Mark a student as excused for an attendance session.",
    tags={"attendance", "professor"},
)
async def excuse_student(
    session_id: str,
    student_id: str,
    reason: str = None,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Excuse a student from attendance.

    Args:
        session_id: The attendance session ID
        student_id: The student's ID
        reason: Optional reason for excusal
        ctx: MCP context for logging

    Returns:
        Dict with update result
    """
    try:
        if ctx:
            await ctx.info(f"Excusing student {student_id}...")

        client = get_client()
        data = {"is_excused": True}
        if reason:
            data["excuse_reason"] = reason

        result = await client.patch(
            f"/api/v2/attendance/sessions/{session_id}/students/{student_id}/excused/",
            data=data,
        )

        if ctx:
            await ctx.info("Student excused successfully")

        return {
            "status": "success",
            "message": "Student excused",
            "session_id": session_id,
            "student_id": student_id,
            "result": result,
        }

    except Exception as e:
        error_msg = f"Failed to excuse student: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)
