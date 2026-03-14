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
    description="Get the schedules (start/due dates) for a drive item.",
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
        Dict with schedule data
    """
    try:
        if ctx:
            await ctx.info(f"Fetching schedules for {item_type} {item_id}...")

        client = get_client()
        result = await client.get(f"/api/v2/drive/items/{item_type}/{item_id}/schedules")

        if ctx:
            await ctx.info("Schedules loaded")

        return {
            "status": "success",
            "item_id": item_id,
            "item_type": item_type,
            "schedules": result.get("schedules", []),
        }

    except Exception as e:
        error_msg = f"Failed to get schedules: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="set_item_schedule",
    description="[PROFESSOR ONLY] Set the schedule (start/due date) for a drive item.",
    tags={"drive", "professor", "schedules"},
)
async def set_item_schedule(
    item_id: str,
    item_type: str,
    start_date: str = None,
    end_date: str = None,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Set schedule for a drive item.

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
            "scope": "all",
            "targets": [],
        }
        if start_date:
            schedule["start_date"] = start_date
        if end_date:
            schedule["end_date"] = end_date

        result = await client.put(
            f"/api/v2/drive/items/{item_type}/{item_id}/schedules",
            data={
                "item_type": item_type,
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
            "result": result,
        }

    except Exception as e:
        error_msg = f"Failed to set schedule: {str(e)}"
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
