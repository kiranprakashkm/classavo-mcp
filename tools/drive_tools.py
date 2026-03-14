"""Drive/Content management tools for Classavo MCP Server.

Handles course content including folders, files, assignments, and playlists.
"""

import logging
from typing import Any, Dict, List, Optional

from fastmcp import Context

from tools import mcp
from auth import get_client

logger = logging.getLogger(__name__)


@mcp.tool(
    name="get_drive_root",
    description="Get the root folder of a course's drive. Shows all top-level content including folders, files, assignments, and playlists.",
    tags={"drive", "professor", "student", "content"},
)
async def get_drive_root(
    public_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get the root folder contents of a course.

    Args:
        public_id: The course public ID (e.g., 'W89PCC4')
        ctx: MCP context for logging

    Returns:
        Dict with root folder and its items
    """
    try:
        if ctx:
            await ctx.info(f"Fetching drive root for course {public_id}...")

        client = get_client()

        # First get root folder ID
        root_info = await client.get(f"/api/courses/{public_id}/folder")
        root_id = root_info.get("identity")

        # Then get folder contents
        result = await client.get(f"/api/folder/{root_id}")

        items = result.get("items", [])

        if ctx:
            await ctx.info(f"Found {len(items)} items in root folder")

        return {
            "status": "success",
            "public_id": public_id,
            "folder": {
                "identity": root_id,
                "title": "Root",
            },
            "item_count": len(items),
            "items": items,
        }

    except Exception as e:
        error_msg = f"Failed to get drive root: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="get_folder_contents",
    description="Get the contents of a specific folder in the course drive.",
    tags={"drive", "professor", "student", "content"},
)
async def get_folder_contents(
    folder_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get contents of a folder.

    Args:
        folder_id: The folder UUID
        ctx: MCP context for logging

    Returns:
        Dict with folder info and items
    """
    try:
        if ctx:
            await ctx.info(f"Fetching folder {folder_id}...")

        client = get_client()
        result = await client.get(f"/api/folder/{folder_id}")

        items = result.get("items", [])

        if ctx:
            await ctx.info(f"Found {len(items)} items in folder")

        return {
            "status": "success",
            "folder": {
                "identity": result.get("identity"),
                "title": result.get("title"),
                "color": result.get("color"),
                "breadcrumb": result.get("breadcrumb", []),
            },
            "item_count": len(items),
            "items": items,
        }

    except Exception as e:
        error_msg = f"Failed to get folder contents: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="create_folder",
    description="[PROFESSOR ONLY] Create a new folder in the course drive.",
    tags={"drive", "professor", "content"},
)
async def create_folder(
    parent_folder_id: str,
    title: str,
    color: str = "#9b59b6",
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Create a new folder.

    Args:
        parent_folder_id: The parent folder UUID
        title: Folder title/name
        color: Folder color hex code (default purple)
        ctx: MCP context for logging

    Returns:
        Dict with created folder data
    """
    try:
        if ctx:
            await ctx.info(f"Creating folder '{title}'...")

        client = get_client()
        result = await client.post(
            f"/api/folder/{parent_folder_id}",
            data={
                "file_type": "folder",
                "title": title,
                "color": color,
            },
        )

        if ctx:
            await ctx.info(f"Folder '{title}' created successfully!")

        return {
            "status": "success",
            "message": f"Folder '{title}' created",
            "folder": result,
        }

    except Exception as e:
        error_msg = f"Failed to create folder: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="update_folder",
    description="[PROFESSOR ONLY] Update a folder's title or color.",
    tags={"drive", "professor", "content"},
)
async def update_folder(
    folder_id: str,
    title: str = None,
    color: str = None,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Update a folder.

    Args:
        folder_id: The folder UUID
        title: New title (optional)
        color: New color hex code (optional)
        ctx: MCP context for logging

    Returns:
        Dict with updated folder data
    """
    try:
        if ctx:
            await ctx.info(f"Updating folder {folder_id}...")

        client = get_client()
        data = {}
        if title:
            data["title"] = title
        if color:
            data["color"] = color

        result = await client.patch(f"/api/folder/{folder_id}", data=data)

        if ctx:
            await ctx.info("Folder updated successfully!")

        return {
            "status": "success",
            "message": "Folder updated",
            "folder": result,
        }

    except Exception as e:
        error_msg = f"Failed to update folder: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="delete_folder",
    description="[PROFESSOR ONLY] Delete a folder from the course drive.",
    tags={"drive", "professor", "content"},
)
async def delete_folder(
    folder_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Delete a folder.

    Args:
        folder_id: The folder UUID
        ctx: MCP context for logging

    Returns:
        Dict with success status
    """
    try:
        if ctx:
            await ctx.info(f"Deleting folder {folder_id}...")

        client = get_client()
        await client.delete(f"/api/folder/{folder_id}")

        if ctx:
            await ctx.info("Folder deleted successfully!")

        return {
            "status": "success",
            "message": "Folder deleted",
            "folder_id": folder_id,
        }

    except Exception as e:
        error_msg = f"Failed to delete folder: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="move_drive_item",
    description="[PROFESSOR ONLY] Move a drive item (file, folder, assignment, playlist) to a different folder.",
    tags={"drive", "professor", "content"},
)
async def move_drive_item(
    item_id: str,
    item_type: str,
    target_folder_id: str,
    index: int = None,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Move a drive item to another folder.

    Args:
        item_id: The item UUID
        item_type: Type of item (file, folder, assignment, playlist)
        target_folder_id: The target folder UUID
        index: Position in target folder (optional)
        ctx: MCP context for logging

    Returns:
        Dict with move result
    """
    try:
        if ctx:
            await ctx.info(f"Moving {item_type} {item_id} to folder {target_folder_id}...")

        client = get_client()
        data = {
            "item_type": item_type,
            "parent_directory_id": target_folder_id,
        }
        if index is not None:
            data["index"] = index

        result = await client.post(f"/api/v2/drive/items/{item_id}/move", data=data)

        if ctx:
            await ctx.info("Item moved successfully!")

        return {
            "status": "success",
            "message": f"{item_type} moved to new folder",
            "item_id": item_id,
            "target_folder_id": target_folder_id,
            "result": result,
        }

    except Exception as e:
        error_msg = f"Failed to move item: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="copy_drive_item",
    description="[PROFESSOR ONLY] Copy a drive item to a different folder.",
    tags={"drive", "professor", "content"},
)
async def copy_drive_item(
    item_id: str,
    item_type: str,
    target_folder_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Copy a drive item to another folder.

    Args:
        item_id: The item UUID
        item_type: Type of item (file, folder, assignment, playlist)
        target_folder_id: The target folder UUID
        ctx: MCP context for logging

    Returns:
        Dict with copy result
    """
    try:
        if ctx:
            await ctx.info(f"Copying {item_type} {item_id} to folder {target_folder_id}...")

        client = get_client()
        result = await client.post(
            f"/api/v2/drive/items/{item_id}/copy",
            data={
                "item_type": item_type,
                "parent_directory_id": target_folder_id,
            },
        )

        if ctx:
            await ctx.info("Item copied successfully!")

        return {
            "status": "success",
            "message": f"{item_type} copied to new folder",
            "original_id": item_id,
            "target_folder_id": target_folder_id,
            "result": result,
        }

    except Exception as e:
        error_msg = f"Failed to copy item: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="get_item_schedules",
    description="Get the schedules (start/due dates) for a drive item. "
    "Shows both class-wide schedules and individual student/section extensions. "
    "Use this to see who has different due dates.",
    tags={"drive", "professor", "student", "schedules"},
)
async def get_item_schedules(
    item_id: str,
    item_type: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get schedules for a drive item.

    Args:
        item_id: The item UUID
        item_type: Type of item (file, folder, assignment, playlist)
        ctx: MCP context for logging

    Returns:
        Dict with schedule data including individual extensions
    """
    try:
        if ctx:
            await ctx.info(f"Fetching schedules for {item_type} {item_id}...")

        # Import timezone utilities
        from utils.timezone import format_due_date, get_user_timezone

        client = get_client()
        result = await client.get(f"/api/v2/drive/items/{item_type}/{item_id}/schedules")

        schedules = result.get("schedules", [])

        # Process schedules to add readable info
        processed_schedules = []
        class_schedule = None
        individual_extensions = []

        for schedule in schedules:
            scope = schedule.get("scope")
            targets = schedule.get("targets", [])
            target_info = schedule.get("target_info", [])
            end_date = schedule.get("end_date")
            start_date = schedule.get("start_date")

            # Format dates
            due_info = format_due_date(end_date)

            processed = {
                "start_date_utc": start_date,
                "end_date_utc": end_date,
                "due_date_local": due_info.get("local"),
                "due_date_relative": due_info.get("relative"),
                "scope": "ALL" if scope == 1 else "INCLUDE",
            }

            if scope == 1:
                # Class-wide schedule
                processed["applies_to"] = "All students"
                class_schedule = processed
            else:
                # Individual or section schedule
                target_names = []
                for ti in target_info:
                    name = ti.get("name") or ti.get("email") or ti.get("target_id")
                    target_type = "Student" if ti.get("target") == 1 else "Section"
                    target_names.append(f"{target_type}: {name}")
                processed["applies_to"] = target_names
                processed["targets"] = targets
                individual_extensions.append(processed)

            processed_schedules.append(processed)

        if ctx:
            ext_count = len(individual_extensions)
            msg = f"Found {len(schedules)} schedule(s)"
            if ext_count > 0:
                msg += f" ({ext_count} individual extension(s))"
            await ctx.info(msg)

        return {
            "status": "success",
            "item_id": item_id,
            "item_type": item_type,
            "timezone": get_user_timezone(),
            "assignment_type": result.get("assignment_type"),
            "class_schedule": class_schedule,
            "individual_extensions": individual_extensions,
            "all_schedules": processed_schedules,
        }

    except Exception as e:
        error_msg = f"Failed to get schedules: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="set_student_due_date",
    description="[PROFESSOR ONLY] Set a different due date for a specific student (extension/accommodation). "
    "This adds an individual schedule for the student while keeping the class-wide due date intact. "
    "Use student_id (UUID) from course roster. For extending a deadline, set end_date to the new due date.",
    tags={"drive", "professor", "schedules", "due_date", "deadline", "extension", "accommodation"},
)
async def set_student_due_date(
    item_id: str,
    item_type: str,
    student_id: str,
    end_date: str,
    start_date: str = None,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Set an individual due date for a specific student.

    This creates or updates an individual schedule for the student while
    preserving the class-wide schedule. Use this for due date extensions
    or accommodations.

    Args:
        item_id: The item UUID (assignment, file, playlist, or folder)
        item_type: Type of item (file, folder, assignment, playlist)
        student_id: The student's UUID (from course roster)
        end_date: New due date in ISO format (e.g., "2025-04-20T23:59:59Z")
        start_date: Optional start date (defaults to same as class)
        ctx: MCP context for logging

    Returns:
        Dict with updated schedules
    """
    try:
        if ctx:
            await ctx.info(f"Setting individual due date for student {student_id}...")

        # Import timezone utilities
        from utils.timezone import format_due_date, get_user_timezone, local_to_utc

        client = get_client()

        # First get current schedules to preserve class-wide schedule
        current = await client.get(f"/api/v2/drive/items/{item_type}/{item_id}/schedules")
        current_schedules = current.get("schedules", [])

        # Find existing class-wide schedule (scope=1)
        class_schedule = None
        other_individual_schedules = []

        for schedule in current_schedules:
            if schedule.get("scope") == 1:
                class_schedule = {
                    "scope": 1,
                    "targets": [],
                    "start_date": schedule.get("start_date"),
                    "end_date": schedule.get("end_date"),
                }
            elif schedule.get("scope") == 2:
                # Check if this is for the same student - if so, we'll replace it
                targets = schedule.get("targets", [])
                is_same_student = any(
                    t.get("target") == 1 and t.get("target_id") == student_id
                    for t in targets
                )
                if not is_same_student:
                    # Keep other individual schedules
                    other_individual_schedules.append({
                        "scope": 2,
                        "targets": targets,
                        "start_date": schedule.get("start_date"),
                        "end_date": schedule.get("end_date"),
                    })

        # Build new schedules array
        new_schedules = []

        # Add class-wide schedule if it exists
        if class_schedule:
            new_schedules.append(class_schedule)
        else:
            # If no class schedule, we need to create one (shouldn't normally happen)
            logger.warning(f"No class-wide schedule found for {item_id}, creating default")

        # Add other existing individual schedules
        new_schedules.extend(other_individual_schedules)

        # Add the new individual schedule for this student
        student_schedule = {
            "scope": 2,  # INCLUDE - specific targets only
            "targets": [
                {
                    "target": 1,  # STUDENT
                    "target_id": student_id,
                }
            ],
            "end_date": end_date,
        }
        if start_date:
            student_schedule["start_date"] = start_date
        elif class_schedule and class_schedule.get("start_date"):
            student_schedule["start_date"] = class_schedule.get("start_date")

        new_schedules.append(student_schedule)

        # Update using assign-v3
        result = await client.post(
            f"/api/v2/drive/items/{item_id}/assign-v3",
            data={
                "item_type": item_type,
                "include_subfolders": False,
                "schedules": new_schedules,
            },
        )

        # Format the due date for response
        due_info = format_due_date(end_date)

        if ctx:
            await ctx.info(f"Individual due date set: {due_info.get('local')}")

        return {
            "status": "success",
            "message": f"Individual due date set for student",
            "item_id": item_id,
            "item_type": item_type,
            "student_id": student_id,
            "new_due_date_utc": end_date,
            "new_due_date_local": due_info.get("local"),
            "timezone": get_user_timezone(),
            "total_schedules": len(new_schedules),
        }

    except Exception as e:
        error_msg = f"Failed to set student due date: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="set_multiple_student_due_dates",
    description="[PROFESSOR ONLY] Set different due dates for multiple students at once. "
    "Provide a JSON array of {student_id, end_date} objects. "
    "Example: [{\"student_id\": \"uuid1\", \"end_date\": \"2025-04-20T23:59:59Z\"}, ...]",
    tags={"drive", "professor", "schedules", "due_date", "deadline", "extension", "accommodation"},
)
async def set_multiple_student_due_dates(
    item_id: str,
    item_type: str,
    student_dates_json: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Set individual due dates for multiple students at once.

    Args:
        item_id: The item UUID (assignment, file, playlist, or folder)
        item_type: Type of item (file, folder, assignment, playlist)
        student_dates_json: JSON array of objects with student_id and end_date
                           e.g., [{"student_id": "uuid", "end_date": "2025-04-20T23:59:59Z"}]
        ctx: MCP context for logging

    Returns:
        Dict with updated schedules
    """
    import json

    try:
        if ctx:
            await ctx.info(f"Setting individual due dates for multiple students...")

        # Parse input
        try:
            student_dates = json.loads(student_dates_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        if not isinstance(student_dates, list):
            raise ValueError("student_dates_json must be a JSON array")

        # Import timezone utilities
        from utils.timezone import format_due_date, get_user_timezone

        client = get_client()

        # Get current schedules
        current = await client.get(f"/api/v2/drive/items/{item_type}/{item_id}/schedules")
        current_schedules = current.get("schedules", [])

        # Find existing class-wide schedule
        class_schedule = None
        for schedule in current_schedules:
            if schedule.get("scope") == 1:
                class_schedule = {
                    "scope": 1,
                    "targets": [],
                    "start_date": schedule.get("start_date"),
                    "end_date": schedule.get("end_date"),
                }
                break

        # Build new schedules array
        new_schedules = []

        # Add class-wide schedule if exists
        if class_schedule:
            new_schedules.append(class_schedule)

        # Build set of new student IDs being set
        new_student_ids = {sd.get("student_id") for sd in student_dates}

        # Keep existing individual schedules for OTHER students
        for schedule in current_schedules:
            if schedule.get("scope") == 2:
                targets = schedule.get("targets", [])
                # Check if any target is a student we're NOT updating
                keep_targets = []
                for t in targets:
                    if t.get("target") == 1 and t.get("target_id") not in new_student_ids:
                        keep_targets.append(t)
                if keep_targets:
                    new_schedules.append({
                        "scope": 2,
                        "targets": keep_targets,
                        "start_date": schedule.get("start_date"),
                        "end_date": schedule.get("end_date"),
                    })

        # Add new individual schedules
        added_students = []
        for sd in student_dates:
            student_id = sd.get("student_id")
            end_date = sd.get("end_date")
            start_date = sd.get("start_date")

            if not student_id or not end_date:
                continue

            student_schedule = {
                "scope": 2,
                "targets": [{"target": 1, "target_id": student_id}],
                "end_date": end_date,
            }
            if start_date:
                student_schedule["start_date"] = start_date
            elif class_schedule and class_schedule.get("start_date"):
                student_schedule["start_date"] = class_schedule.get("start_date")

            new_schedules.append(student_schedule)
            added_students.append({
                "student_id": student_id,
                "end_date": end_date,
                "due_date_local": format_due_date(end_date).get("local"),
            })

        # Update using assign-v3
        result = await client.post(
            f"/api/v2/drive/items/{item_id}/assign-v3",
            data={
                "item_type": item_type,
                "include_subfolders": False,
                "schedules": new_schedules,
            },
        )

        if ctx:
            await ctx.info(f"Set individual due dates for {len(added_students)} students")

        return {
            "status": "success",
            "message": f"Individual due dates set for {len(added_students)} students",
            "item_id": item_id,
            "item_type": item_type,
            "timezone": get_user_timezone(),
            "students_updated": added_students,
            "total_schedules": len(new_schedules),
        }

    except Exception as e:
        error_msg = f"Failed to set student due dates: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="remove_student_due_date",
    description="[PROFESSOR ONLY] Remove an individual due date extension for a student, "
    "reverting them to the class-wide due date.",
    tags={"drive", "professor", "schedules", "due_date", "extension"},
)
async def remove_student_due_date(
    item_id: str,
    item_type: str,
    student_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Remove an individual due date for a student.

    Args:
        item_id: The item UUID
        item_type: Type of item (file, folder, assignment, playlist)
        student_id: The student's UUID
        ctx: MCP context for logging

    Returns:
        Dict with updated schedules
    """
    try:
        if ctx:
            await ctx.info(f"Removing individual due date for student {student_id}...")

        client = get_client()

        # Get current schedules
        current = await client.get(f"/api/v2/drive/items/{item_type}/{item_id}/schedules")
        current_schedules = current.get("schedules", [])

        # Build new schedules excluding this student's individual schedule
        new_schedules = []
        removed = False

        for schedule in current_schedules:
            if schedule.get("scope") == 1:
                # Keep class-wide schedule
                new_schedules.append({
                    "scope": 1,
                    "targets": [],
                    "start_date": schedule.get("start_date"),
                    "end_date": schedule.get("end_date"),
                })
            elif schedule.get("scope") == 2:
                # Check targets - exclude this student
                targets = schedule.get("targets", [])
                remaining_targets = []
                for t in targets:
                    if t.get("target") == 1 and t.get("target_id") == student_id:
                        removed = True
                    else:
                        remaining_targets.append(t)

                # Keep schedule if there are remaining targets
                if remaining_targets:
                    new_schedules.append({
                        "scope": 2,
                        "targets": remaining_targets,
                        "start_date": schedule.get("start_date"),
                        "end_date": schedule.get("end_date"),
                    })

        if not removed:
            return {
                "status": "warning",
                "message": "No individual due date found for this student",
                "item_id": item_id,
                "student_id": student_id,
            }

        # Update using assign-v3
        result = await client.post(
            f"/api/v2/drive/items/{item_id}/assign-v3",
            data={
                "item_type": item_type,
                "include_subfolders": False,
                "schedules": new_schedules,
            },
        )

        if ctx:
            await ctx.info("Individual due date removed")

        return {
            "status": "success",
            "message": "Individual due date removed - student now follows class schedule",
            "item_id": item_id,
            "item_type": item_type,
            "student_id": student_id,
        }

    except Exception as e:
        error_msg = f"Failed to remove student due date: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="set_item_schedule",
    description="[PROFESSOR ONLY] Set or update the class-wide schedule (start date and due date) for a drive item. "
    "Use this to assign due dates to assignments, files, folders, or playlists. "
    "For individual student extensions, use set_student_due_date instead.",
    tags={"drive", "professor", "schedules", "due_date", "deadline"},
)
async def set_item_schedule(
    item_id: str,
    item_type: str,
    start_date: str = None,
    end_date: str = None,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Set schedule (start/due date) for a drive item.

    Args:
        item_id: The item UUID
        item_type: Type of item (file, folder, assignment, playlist)
        start_date: Start date in ISO format (e.g., "2024-03-15T09:00:00Z")
        end_date: Due date in ISO format (e.g., "2024-03-22T23:59:59Z")
        ctx: MCP context for logging

    Returns:
        Dict with updated schedule
    """
    try:
        if ctx:
            await ctx.info(f"Setting schedule for {item_type} {item_id}...")

        client = get_client()

        schedule = {
            "scope": 1,  # 1 = all students
            "targets": [],
        }
        if start_date:
            schedule["start_date"] = start_date
        if end_date:
            schedule["end_date"] = end_date

        # Use assign-v3 endpoint which works for setting schedules
        result = await client.post(
            f"/api/v2/drive/items/{item_id}/assign-v3",
            data={
                "item_type": item_type,
                "include_subfolders": False,
                "schedules": [schedule],
            },
        )

        if ctx:
            await ctx.info("Schedule updated!")

        return {
            "status": "success",
            "message": "Schedule updated",
            "item_id": item_id,
            "item_type": item_type,
            "start_date": start_date,
            "end_date": end_date,
            "result": result,
        }

    except Exception as e:
        error_msg = f"Failed to set schedule: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="remove_item_schedule",
    description="[PROFESSOR ONLY] Remove the schedule (unassign) from a drive item.",
    tags={"drive", "professor", "schedules"},
)
async def remove_item_schedule(
    item_id: str,
    item_type: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Remove schedule from a drive item.

    Args:
        item_id: The item UUID
        item_type: Type of item (file, folder, assignment, playlist)
        ctx: MCP context for logging

    Returns:
        Dict with result
    """
    try:
        if ctx:
            await ctx.info(f"Removing schedule from {item_type} {item_id}...")

        client = get_client()

        # Set empty schedules to remove assignment
        result = await client.post(
            f"/api/v2/drive/items/{item_id}/assign-v3",
            data={
                "item_type": item_type,
                "include_subfolders": False,
                "schedules": [],
            },
        )

        if ctx:
            await ctx.info("Schedule removed!")

        return {
            "status": "success",
            "message": "Schedule removed",
            "item_id": item_id,
            "item_type": item_type,
            "result": result,
        }

    except Exception as e:
        error_msg = f"Failed to remove schedule: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="get_assigned_items",
    description="Get all assigned/scheduled items for a course.",
    tags={"drive", "professor", "student", "content"},
)
async def get_assigned_items(
    public_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get all assigned items for a course.

    Args:
        public_id: The course public ID
        ctx: MCP context for logging

    Returns:
        Dict with assigned items
    """
    try:
        if ctx:
            await ctx.info(f"Fetching assigned items for course {public_id}...")

        client = get_client()
        result = await client.get(f"/api/v2/drive/courses/{public_id}/assigned-items/")

        items = result if isinstance(result, list) else result.get("results", [])

        if ctx:
            await ctx.info(f"Found {len(items)} assigned items")

        return {
            "status": "success",
            "public_id": public_id,
            "count": len(items),
            "items": items,
        }

    except Exception as e:
        error_msg = f"Failed to get assigned items: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="list_playlists",
    description="List all playlists for a course.",
    tags={"drive", "professor", "student", "playlists"},
)
async def list_playlists(
    public_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    List playlists for a course.

    Args:
        public_id: The course public ID
        ctx: MCP context for logging

    Returns:
        Dict with playlists
    """
    try:
        if ctx:
            await ctx.info(f"Fetching playlists for course {public_id}...")

        client = get_client()
        result = await client.get(f"/api/v2/drive/courses/{public_id}/playlists/list/")

        playlists = result if isinstance(result, list) else result.get("results", [])

        if ctx:
            await ctx.info(f"Found {len(playlists)} playlists")

        return {
            "status": "success",
            "public_id": public_id,
            "count": len(playlists),
            "playlists": playlists,
        }

    except Exception as e:
        error_msg = f"Failed to list playlists: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="get_playlist",
    description="Get details of a specific playlist including its items.",
    tags={"drive", "professor", "student", "playlists"},
)
async def get_playlist(
    public_id: str,
    playlist_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get playlist details.

    Args:
        public_id: The course public ID
        playlist_id: The playlist UUID
        ctx: MCP context for logging

    Returns:
        Dict with playlist details and items
    """
    try:
        if ctx:
            await ctx.info(f"Fetching playlist {playlist_id}...")

        client = get_client()
        result = await client.get(f"/api/v2/drive/courses/{public_id}/playlists/{playlist_id}/")

        if ctx:
            await ctx.info("Playlist loaded")

        return {
            "status": "success",
            "playlist": result,
        }

    except Exception as e:
        error_msg = f"Failed to get playlist: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="get_playlist_items",
    description="Get all items in a playlist.",
    tags={"drive", "professor", "student", "playlists"},
)
async def get_playlist_items(
    public_id: str,
    playlist_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get items in a playlist.

    Args:
        public_id: The course public ID
        playlist_id: The playlist UUID
        ctx: MCP context for logging

    Returns:
        Dict with playlist items
    """
    try:
        if ctx:
            await ctx.info(f"Fetching items for playlist {playlist_id}...")

        client = get_client()
        result = await client.get(f"/api/v2/drive/courses/{public_id}/playlists/{playlist_id}/items/")

        items = result if isinstance(result, list) else result.get("results", [])

        if ctx:
            await ctx.info(f"Found {len(items)} items in playlist")

        return {
            "status": "success",
            "playlist_id": playlist_id,
            "count": len(items),
            "items": items,
        }

    except Exception as e:
        error_msg = f"Failed to get playlist items: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="update_playlist_title",
    description="[PROFESSOR ONLY] Update a playlist's title.",
    tags={"drive", "professor", "playlists"},
)
async def update_playlist_title(
    public_id: str,
    playlist_id: str,
    title: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Update playlist title.

    Args:
        public_id: The course public ID
        playlist_id: The playlist UUID
        title: New playlist title
        ctx: MCP context for logging

    Returns:
        Dict with updated playlist
    """
    try:
        if ctx:
            await ctx.info(f"Updating playlist title to '{title}'...")

        client = get_client()
        result = await client.patch(
            f"/api/v2/drive/courses/{public_id}/playlists/{playlist_id}/title/",
            data={"title": title},
        )

        if ctx:
            await ctx.info("Playlist title updated!")

        return {
            "status": "success",
            "message": f"Playlist title updated to '{title}'",
            "playlist_id": playlist_id,
            "result": result,
        }

    except Exception as e:
        error_msg = f"Failed to update playlist title: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="delete_playlist",
    description="[PROFESSOR ONLY] Delete a playlist.",
    tags={"drive", "professor", "playlists"},
)
async def delete_playlist(
    public_id: str,
    playlist_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Delete a playlist.

    Args:
        public_id: The course public ID
        playlist_id: The playlist UUID
        ctx: MCP context for logging

    Returns:
        Dict with success status
    """
    try:
        if ctx:
            await ctx.info(f"Deleting playlist {playlist_id}...")

        client = get_client()
        await client.delete(f"/api/v2/drive/courses/{public_id}/playlists/{playlist_id}/delete/")

        if ctx:
            await ctx.info("Playlist deleted!")

        return {
            "status": "success",
            "message": "Playlist deleted",
            "playlist_id": playlist_id,
        }

    except Exception as e:
        error_msg = f"Failed to delete playlist: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)
