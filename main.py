#!/usr/bin/env python3
"""Classavo MCP Server - AI-powered education platform integration.

This MCP server enables Claude Desktop and other MCP clients to interact
with Classavo's education platform via natural language.

Features:
- Course management for professors and students
- Assignment creation and submission
- Automated grading and feedback
- Attendance tracking with codes
- Live polling for classroom engagement
- Discussion boards
- Gradebook and analytics

Privacy Controls:
- Students can only view their OWN grades, submissions, and attendance
- Role-based tool access (Professor vs Student)
- API-level permission enforcement
"""

import logging
import sys

from fastmcp import FastMCP

from config import config
from tools import init_tools
from auth import auto_login

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if config.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastMCP server
mcp = FastMCP(
    name="Classavo MCP Server",
    instructions="""AI assistant for Classavo education platform.

You help professors and students interact with their courses, assignments,
grades, attendance, and more through natural language.

AVAILABLE CAPABILITIES:

FOR PROFESSORS:
1. Courses - Create, manage, and view course rosters
2. Assignments - Create, update, and manage assignments/quizzes
3. Grading - View submissions, grade work, provide feedback
4. Attendance - Start sessions, generate codes, track attendance
5. Polling - Create and run live polls during class
6. Discussions - Create threads, manage comments, pin answers
7. Analytics - View course insights and gradebook exports

FOR STUDENTS:
1. View YOUR grades (only your own, not other students')
2. Submit assignments
3. Check in to attendance with codes
4. Vote in polls
5. Participate in discussions
6. View chapter content

PRIVACY NOTICE:
Students can only access their own data. Grades, submissions, and attendance
records are private and not shared between students.

GETTING STARTED:
1. Use 'login' with your Classavo credentials, OR
2. Set CLASSAVO_API_TOKEN environment variable

Then try:
- "List my courses"
- "Show assignments for course X"
- "What are my grades in Chemistry?"
- "Start attendance for today's class"
""",
)

# Initialize all tools
init_tools(mcp)


async def startup():
    """Perform startup tasks."""
    logger.info("Starting Classavo MCP Server...")

    # Auto-login if credentials are configured
    if config.username and config.password:
        try:
            await auto_login()
            logger.info("Auto-login successful")
        except Exception as e:
            logger.warning(f"Auto-login failed: {e}. Manual login required.")
    elif config.api_token:
        logger.info("Using pre-configured API token")
    else:
        logger.info("No credentials configured. Use 'login' tool to authenticate.")

    logger.info("Classavo MCP Server ready!")


def main():
    """Main entry point."""
    try:
        # Run startup tasks
        import asyncio

        asyncio.run(startup())
    except Exception as e:
        logger.warning(f"Startup warning: {e}")

    # Run the MCP server
    mcp.run()


if __name__ == "__main__":
    main()
