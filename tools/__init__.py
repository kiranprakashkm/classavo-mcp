"""Tool registration for Classavo MCP Server."""

from typing import Optional
from fastmcp import FastMCP

# Global reference to MCP server instance
mcp: Optional[FastMCP] = None


def init_tools(server_instance: FastMCP) -> None:
    """
    Initialize all tools with the FastMCP server instance.

    Args:
        server_instance: The FastMCP server to register tools with
    """
    global mcp
    mcp = server_instance

    # Import all tool modules to trigger @mcp.tool() registration
    from . import auth_tools
    from . import course_tools
    from . import assignment_tools
    from . import grading_tools
    from . import attendance_tools
    from . import polling_tools
    from . import discussion_tools
    from . import student_tools
