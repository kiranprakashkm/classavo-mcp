# Classavo MCP Server

A Model Context Protocol (MCP) server that enables AI assistants like Claude Desktop to interact with the Classavo education platform via natural language.

## Features

### For Professors
- **Course Management** - Create courses, manage rosters, invite students
- **Assignments** - Create, update, clone assignments and quizzes
- **Grading** - View submissions, grade work, provide feedback
- **Attendance** - Start sessions, generate codes, track attendance
- **Live Polling** - Create and run polls during class
- **Discussions** - Create threads, pin comments, manage discussions
- **Analytics** - View insights, export gradebook to LMS formats

### For Students
- **View Grades** - See YOUR grades (privacy protected)
- **Submit Work** - Submit assignments
- **Attendance** - Check in with attendance codes
- **Polling** - Vote in active polls
- **Discussions** - Participate in discussions
- **Content** - View course chapters and materials

## Privacy Controls

**Important:** This server implements strict privacy controls:
- Students can ONLY view their own grades, submissions, and attendance
- Student tools do not accept `student_id` parameters
- API endpoints return only the authenticated user's data
- Professor-only tools verify user role before execution

## Installation

### Prerequisites
- Python 3.10+
- A Classavo account (Professor or Student)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/kiranprakashkm/classavo-mcp.git
cd classavo-mcp
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

### Environment Variables

Create a `.env` file or set these environment variables:

```bash
# Classavo API URL (production or local)
CLASSAVO_API_URL=https://api.classavo.com

# Option 1: Pre-configured API token
CLASSAVO_API_TOKEN=your_token_here

# Option 2: Username/password for login flow
CLASSAVO_USERNAME=your_email@example.com
CLASSAVO_PASSWORD=your_password

# Optional settings
CLASSAVO_RATE_LIMIT=10  # Requests per second
DEBUG=false
```

### Claude Desktop Configuration

Add to `~/.config/claude/claude_desktop_config.json` (macOS/Linux) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "classavo": {
      "command": "python",
      "args": ["/path/to/classavo-mcp/main.py"],
      "env": {
        "CLASSAVO_API_URL": "https://api.classavo.com",
        "CLASSAVO_USERNAME": "your_email@example.com",
        "CLASSAVO_PASSWORD": "your_password"
      }
    }
  }
}
```

Alternatively, use an API token:

```json
{
  "mcpServers": {
    "classavo": {
      "command": "python",
      "args": ["/path/to/classavo-mcp/main.py"],
      "env": {
        "CLASSAVO_API_URL": "https://api.classavo.com",
        "CLASSAVO_API_TOKEN": "your_api_token_here"
      }
    }
  }
}
```

## Running the Server

### Standalone
```bash
python main.py
```

### With Claude Desktop
After configuring Claude Desktop, restart it. The Classavo tools will be available automatically.

## Available Tools

### Authentication
| Tool | Description |
|------|-------------|
| `login` | Authenticate with username/password |
| `logout` | End session |
| `get_my_profile` | View current user info |
| `get_notifications` | View notifications |

### Courses
| Tool | Description | Access |
|------|-------------|--------|
| `list_courses` | List your courses | All |
| `get_course` | Get course details | All |
| `create_course` | Create a new course | Professor |
| `get_course_roster` | View enrolled students | Professor |
| `invite_students` | Invite students by email | Professor |
| `join_course` | Join with invite code | Student |
| `get_course_analytics` | View course insights | Professor |

### Assignments
| Tool | Description | Access |
|------|-------------|--------|
| `list_assignments` | List assignments | All |
| `get_assignment` | Get assignment details | All |
| `create_assignment` | Create assignment | Professor |
| `update_assignment` | Update assignment | Professor |
| `delete_assignment` | Delete assignment | Professor |
| `create_question` | Add question to assignment | Professor |
| `clone_assignment` | Clone to another course | Professor |

### Grading & Submissions
| Tool | Description | Access |
|------|-------------|--------|
| `list_submissions` | View all submissions | Professor |
| `get_submission` | View submission details | Professor |
| `grade_submission` | Grade a submission | Professor |
| `get_gradebook` | Full gradebook | Professor |
| `export_gradebook` | Export to LMS format | Professor |
| `view_my_grades` | Your grades only | Student |
| `view_my_submissions` | Your submissions only | Student |
| `submit_assignment` | Submit your work | Student |

### Attendance
| Tool | Description | Access |
|------|-------------|--------|
| `start_attendance_session` | Start attendance | Professor |
| `end_attendance_session` | End session | Professor |
| `get_active_sessions` | View active sessions | Professor |
| `get_attendance_report` | Attendance report | Professor |
| `mark_student_attendance` | Manual marking | Professor |
| `check_in_attendance` | Check in with code | Student |
| `view_my_attendance` | Your attendance | Student |

### Polling
| Tool | Description | Access |
|------|-------------|--------|
| `list_polls` | List polls | Professor |
| `create_poll` | Create a poll | Professor |
| `start_poll` | Launch poll | Professor |
| `end_poll` | End poll | Professor |
| `get_poll_results` | View results | Professor |
| `vote_in_poll` | Cast your vote | Student |
| `get_active_polls` | View active polls | Student |

### Discussions
| Tool | Description | Access |
|------|-------------|--------|
| `list_discussions` | List discussions | All |
| `get_discussion` | View discussion | All |
| `create_discussion` | Create thread | Professor |
| `post_comment` | Add comment | All |
| `pin_comment` | Pin comment | Professor |
| `delete_discussion` | Delete thread | Professor |

### Search
| Tool | Description | Access |
|------|-------------|--------|
| `global_search` | Search across courses | All |

## Example Usage

### Professor Examples

```
"List all my courses"
"Show the roster for Chemistry 101"
"Create a homework assignment called 'Chapter 5 Review' for course abc123"
"Start attendance for my Biology class"
"How did students do on the midterm exam?"
"Export grades to Canvas format"
```

### Student Examples

```
"What are my grades in Chemistry?"
"Show my upcoming deadlines"
"Check me in with attendance code 1234"
"Submit my homework for assignment xyz"
"Vote option B in the current poll"
```

## Development

### Running Tests
```bash
pytest
pytest --cov=. --cov-report=term-missing
```

### Project Structure
```
classavo-mcp/
├── main.py              # FastMCP server entry point
├── config.py            # Environment configuration
├── client.py            # Async HTTP client for Classavo API
├── auth.py              # Authentication management
├── tools/
│   ├── __init__.py      # Tool registration
│   ├── auth_tools.py    # Login, profile, notifications
│   ├── course_tools.py  # Course CRUD, roster
│   ├── assignment_tools.py  # Assignment management
│   ├── grading_tools.py     # Submissions, grading
│   ├── attendance_tools.py  # Attendance tracking
│   ├── polling_tools.py     # Live polls
│   ├── discussion_tools.py  # Discussion boards
│   └── student_tools.py     # Student-specific (privacy protected)
├── requirements.txt
├── README.md
└── PLAN.md
```

## License

MIT License - See LICENSE file for details.

## Support

For issues or questions:
- Open an issue on GitHub
- Contact the Classavo support team
