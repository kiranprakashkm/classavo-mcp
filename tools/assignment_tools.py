"""Assignment management tools for Classavo MCP Server."""

import logging
from typing import Any, Dict, List, Optional

from fastmcp import Context

from tools import mcp
from auth import get_client

logger = logging.getLogger(__name__)


@mcp.tool(
    name="list_assignments",
    description="List all assignments for a course with due dates. Use the course public_id (e.g., 'WMYDQWU'), not the UUID.",
    tags={"assignments", "professor", "student"},
)
async def list_assignments(
    public_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    List all assignments for a course with due dates from schedules.

    Args:
        public_id: The course public ID (e.g., 'WMYDQWU')
        ctx: MCP context for logging

    Returns:
        Dict with list of assignments including due dates
    """
    try:
        if ctx:
            await ctx.info(f"Fetching assignments for course {public_id}...")

        client = get_client()

        # Get assignments list
        result = await client.get(f"/api/courses/{public_id}/assignments")
        assignments = result if isinstance(result, list) else result.get("results", result.get("assignments", []))

        # Get scheduled tasks (contains actual due dates)
        try:
            tasks_result = await client.get(f"/api/v2/dashboard/{public_id}/tasks/")
            tasks = tasks_result.get("results", []) if isinstance(tasks_result, dict) else tasks_result

            # Build a map of assignment identity -> schedule info
            schedule_map = {}
            for task in tasks:
                if task.get("item_type") == "assignment" and task.get("schedules"):
                    identity = task.get("identity")
                    schedules = task.get("schedules", [])
                    if schedules:
                        # Use the first schedule's end_date as due date
                        schedule_map[identity] = {
                            "due_date": schedules[0].get("end_date"),
                            "start_date": schedules[0].get("start_date"),
                            "schedules": schedules,
                        }

            # Merge schedule info into assignments
            for assignment in assignments:
                identity = assignment.get("identity")
                if identity in schedule_map:
                    assignment["due_date"] = schedule_map[identity]["due_date"]
                    assignment["start_date"] = schedule_map[identity]["start_date"]
                    assignment["has_schedule"] = True
                else:
                    assignment["due_date"] = assignment.get("effective_due_date")
                    assignment["has_schedule"] = False

        except Exception as e:
            # If tasks endpoint fails, continue with assignments only
            logger.warning(f"Could not fetch scheduled tasks: {e}")
            for assignment in assignments:
                assignment["due_date"] = assignment.get("effective_due_date")
                assignment["has_schedule"] = False

        if ctx:
            await ctx.info(f"Found {len(assignments)} assignments")

        return {
            "status": "success",
            "public_id": public_id,
            "count": len(assignments),
            "assignments": assignments,
        }

    except Exception as e:
        error_msg = f"Failed to list assignments: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="get_assignment",
    description="Get detailed information about a specific assignment.",
    tags={"assignments", "professor", "student"},
)
async def get_assignment(
    assignment_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get assignment details.

    Args:
        assignment_id: The assignment ID
        ctx: MCP context for logging

    Returns:
        Dict with assignment details
    """
    try:
        if ctx:
            await ctx.info(f"Fetching assignment {assignment_id}...")

        client = get_client()
        result = await client.get(f"/api/assignments/{assignment_id}")

        if ctx:
            await ctx.info(f"Found assignment: {result.get('name', 'Unknown')}")

        return {
            "status": "success",
            "assignment": result,
        }

    except Exception as e:
        error_msg = f"Failed to get assignment: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="create_assignment",
    description="[PROFESSOR ONLY] Create a new assignment for a course.",
    tags={"assignments", "professor"},
)
async def create_assignment(
    course_id: str,
    name: str,
    description: str = "",
    due_date: str = None,
    points: int = 100,
    assignment_type: str = "homework",
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Create a new assignment.

    Args:
        course_id: The course ID
        name: Assignment name (e.g., "Homework 5")
        description: Assignment description/instructions
        due_date: Due date in ISO format (e.g., "2024-12-31T23:59:00Z")
        points: Total points (default 100)
        assignment_type: Type of assignment (homework, quiz, exam, etc.)
        ctx: MCP context for logging

    Returns:
        Dict with created assignment data
    """
    try:
        if ctx:
            await ctx.info(f"Creating assignment: {name}...")

        client = get_client()
        data = {
            "course": course_id,
            "name": name,
            "description": description,
            "points": points,
            "assignment_type": assignment_type,
        }
        if due_date:
            data["due_date"] = due_date

        result = await client.post(f"/api/courses/{course_id}/assignments", data=data)

        if ctx:
            await ctx.info(f"Assignment '{name}' created successfully!")

        return {
            "status": "success",
            "message": f"Assignment '{name}' created",
            "assignment": result,
        }

    except Exception as e:
        error_msg = f"Failed to create assignment: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="update_assignment",
    description="[PROFESSOR ONLY] Update an existing assignment.",
    tags={"assignments", "professor"},
)
async def update_assignment(
    assignment_id: str,
    name: str = None,
    description: str = None,
    due_date: str = None,
    points: int = None,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Update an assignment.

    Args:
        assignment_id: The assignment ID
        name: New name (optional)
        description: New description (optional)
        due_date: New due date (optional)
        points: New point value (optional)
        ctx: MCP context for logging

    Returns:
        Dict with updated assignment data
    """
    try:
        if ctx:
            await ctx.info(f"Updating assignment {assignment_id}...")

        client = get_client()
        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if due_date is not None:
            data["due_date"] = due_date
        if points is not None:
            data["points"] = points

        result = await client.patch(f"/api/assignments/{assignment_id}", data=data)

        if ctx:
            await ctx.info("Assignment updated successfully!")

        return {
            "status": "success",
            "message": "Assignment updated",
            "assignment": result,
        }

    except Exception as e:
        error_msg = f"Failed to update assignment: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="delete_assignment",
    description="[PROFESSOR ONLY] Delete an assignment.",
    tags={"assignments", "professor"},
)
async def delete_assignment(
    assignment_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Delete an assignment.

    Args:
        assignment_id: The assignment ID
        ctx: MCP context for logging

    Returns:
        Dict with success status
    """
    try:
        if ctx:
            await ctx.info(f"Deleting assignment {assignment_id}...")

        client = get_client()
        await client.delete(f"/api/assignments/{assignment_id}")

        if ctx:
            await ctx.info("Assignment deleted successfully!")

        return {
            "status": "success",
            "message": "Assignment deleted",
            "assignment_id": assignment_id,
        }

    except Exception as e:
        error_msg = f"Failed to delete assignment: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="get_assignment_questions",
    description="Get all questions for an assignment.",
    tags={"assignments", "professor", "student"},
)
async def get_assignment_questions(
    assignment_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get questions for an assignment.

    Args:
        assignment_id: The assignment ID
        ctx: MCP context for logging

    Returns:
        Dict with list of questions
    """
    try:
        if ctx:
            await ctx.info(f"Fetching questions for assignment {assignment_id}...")

        client = get_client()
        result = await client.get(f"/api/assignments/{assignment_id}/questions")

        questions = result if isinstance(result, list) else result.get("questions", [])

        if ctx:
            await ctx.info(f"Found {len(questions)} questions")

        return {
            "status": "success",
            "assignment_id": assignment_id,
            "count": len(questions),
            "questions": questions,
        }

    except Exception as e:
        error_msg = f"Failed to get questions: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="create_question",
    description="[PROFESSOR ONLY] Add a question to an assignment. "
    "Types: multiple_choice, fill_blank, written, equation, discussion",
    tags={"assignments", "professor", "questions"},
)
async def create_question(
    assignment_id: str,
    question_text: str,
    question_type: str = "multiple_choice",
    points: int = 10,
    options: str = None,
    correct_answer: str = None,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Create a question for an assignment.

    Args:
        assignment_id: The assignment ID
        question_text: The question text
        question_type: Type (multiple_choice, fill_blank, written, equation, discussion)
        points: Point value for this question
        options: Comma-separated options for multiple choice (e.g., "A,B,C,D")
        correct_answer: The correct answer
        ctx: MCP context for logging

    Returns:
        Dict with created question data
    """
    try:
        if ctx:
            await ctx.info(f"Creating {question_type} question...")

        client = get_client()

        # Map question types to API values
        type_map = {
            "multiple_choice": 1,
            "fill_blank": 2,
            "written": 3,
            "equation": 4,
            "discussion": 5,
        }
        q_type = type_map.get(question_type, 1)

        data = {
            "assignment": assignment_id,
            "question_text": question_text,
            "question_type": q_type,
            "points": points,
        }

        if options and question_type == "multiple_choice":
            option_list = [o.strip() for o in options.split(",")]
            data["options"] = [{"text": opt} for opt in option_list]

        if correct_answer:
            data["correct_answer"] = correct_answer

        result = await client.post(f"/api/assignments/{assignment_id}/questions", data=data)

        if ctx:
            await ctx.info("Question created successfully!")

        return {
            "status": "success",
            "message": "Question created",
            "question": result,
        }

    except Exception as e:
        error_msg = f"Failed to create question: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="clone_assignment",
    description="[PROFESSOR ONLY] Clone an assignment to the same or another course.",
    tags={"assignments", "professor", "clone"},
)
async def clone_assignment(
    assignment_id: str,
    target_course_id: str = None,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Clone an assignment.

    Args:
        assignment_id: The assignment ID to clone
        target_course_id: Target course ID (optional, same course if not provided)
        ctx: MCP context for logging

    Returns:
        Dict with cloned assignment data
    """
    try:
        if ctx:
            await ctx.info(f"Cloning assignment {assignment_id}...")

        client = get_client()
        data = {}
        if target_course_id:
            data["target_course"] = target_course_id

        result = await client.post(f"/api/assignments/{assignment_id}/clone", data=data)

        if ctx:
            await ctx.info("Assignment cloned successfully!")

        return {
            "status": "success",
            "message": "Assignment cloned",
            "original_id": assignment_id,
            "cloned_assignment": result,
        }

    except Exception as e:
        error_msg = f"Failed to clone assignment: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)
