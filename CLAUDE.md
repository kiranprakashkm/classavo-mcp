# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Classavo MCP Server - A Model Context Protocol server enabling AI-powered interaction with Classavo's education platform through Claude Desktop. Built with FastMCP for professors and students.

## Commands

### Development Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run the Server
```bash
python main.py
```

### Run Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=. --cov-report=term-missing

# Verbose output
pytest -v
```

## Architecture

The server follows a modular tool-based architecture:

```
main.py                  # FastMCP server entry point, initializes tools
├── config.py            # ClassavoConfig class loads env vars
├── client.py            # ClassavoClient for async HTTP API calls
├── auth.py              # Token management, auto-login, role detection
└── tools/
    ├── __init__.py      # init_tools() registers all tool modules
    ├── auth_tools.py    # login, logout, profile, notifications
    ├── course_tools.py  # Course CRUD, roster, invitations
    ├── assignment_tools.py  # Assignment/question management
    ├── grading_tools.py     # Submissions, grading, gradebook export
    ├── attendance_tools.py  # Attendance sessions and tracking
    ├── polling_tools.py     # Live polling for class engagement
    ├── discussion_tools.py  # Discussion boards and comments
    └── student_tools.py     # Student-specific tools (privacy protected)
```

### Tool Registration Pattern

Tools are defined as async functions decorated with `@mcp.tool()` in each module. The `init_tools()` function in `tools/__init__.py` imports all modules to trigger registration:

```python
from tools import init_tools
mcp = FastMCP(name="Classavo MCP Server", ...)
init_tools(mcp)
```

Each tool module accesses the global `mcp` instance from `tools/__init__.py`.

### Privacy Controls

**Critical**: Students must NOT see other students' grades, submissions, or attendance.

Implementation:
1. Student tools do NOT accept `student_id` parameters
2. API endpoints use `student=me` to return only authenticated user's data
3. Professor-only tools check user role before execution
4. Tools are tagged with `professor`, `student`, or both

## Configuration

Environment variables (set in Claude Desktop config or .env):
- `CLASSAVO_API_URL` - Classavo API URL (e.g., https://api.classavo.com)
- `CLASSAVO_API_TOKEN` - Pre-configured API token (optional)
- `CLASSAVO_USERNAME` - Username for login flow (optional)
- `CLASSAVO_PASSWORD` - Password for login flow (optional)
- `CLASSAVO_RATE_LIMIT` - Requests per second (default: 10)
- `DEBUG` - Enable debug logging (true/false)

## Testing

Tests use pytest with:
- `respx` for mocking HTTP requests
- `faker` for generating test data
- Fixtures in `tests/conftest.py` provide mock clients, contexts, and sample data

## API Endpoints

Classavo uses Django REST Framework with Token authentication:
- Header: `Authorization: Token {token}`
- User roles: 1 = Student, 2 = Professor

Key endpoint patterns:
- `/api/v2/courses/` - Course management
- `/api/assignments/` - Assignment CRUD
- `/api/v2/submissions/` - Submission handling
- `/api/v2/attendance/` - Attendance tracking
- `/api/v2/polling/` - Live polls
- `/api/discussions/` - Discussion boards
- `/api/v2/gradebook/` - Grade management
