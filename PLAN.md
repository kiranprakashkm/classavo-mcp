# Classavo MCP Server - Implementation Plan

## Overview
Build a standalone MCP server that connects Claude Desktop/ChatGPT to Classavo's Django+React education platform via their existing REST API.

## What is Classavo?
**All-in-one teaching platform** for higher education featuring:
- Smart digital textbooks with marketplace (OpenStax, Saylor)
- Auto-grading assignments & AI-powered feedback
- Real-time analytics dashboard
- Attendance tracking (SMS codes, geolocation)
- Live polling & discussion boards
- Exam proctoring capabilities
- LMS integration (Canvas, Blackboard, etc.)

**Two user types:** Professors (free) and Students (paid subscription)

## Approach: Standalone FastMCP Server (Recommended)
- **Why**: Freelance project, no control over Classavo's Django codebase
- **How**: Build separate MCP server that wraps their API (same pattern as PhysicianX SendGrid MCP)
- **Benefit**: Deliverable today, zero changes to Classavo's system

---

## Project Structure

```
classavo-mcp/
├── main.py                 # FastMCP server entry point
├── config.py               # Environment config (API URL, token)
├── auth.py                 # Token auth (login flow or API token)
├── client.py               # Async HTTP client for Classavo API
├── tools/
│   ├── __init__.py         # Tool registration
│   ├── auth_tools.py       # Login, get profile, logout
│   ├── course_tools.py     # Course CRUD, list courses
│   ├── assignment_tools.py # Assignment management
│   ├── grading_tools.py    # View/grade submissions
│   ├── attendance_tools.py # Attendance tracking
│   ├── polling_tools.py    # Live polling
│   ├── discussion_tools.py # Discussion boards
│   └── student_tools.py    # Student-specific tools
├── requirements.txt
├── README.md
└── tests/
    └── conftest.py
```

---

## Phase 1: Core Infrastructure (1-2 hours)

### 1.1 Create new repository
```bash
mkdir classavo-mcp && cd classavo-mcp
git init
python3 -m venv venv && source venv/bin/activate
```

### 1.2 config.py - Environment Configuration
```python
# Environment variables:
# - CLASSAVO_API_URL (e.g., https://api.classavo.com or http://localhost:8000)
# - CLASSAVO_API_TOKEN (optional, if pre-authenticated)
# - CLASSAVO_USERNAME (for login flow)
# - CLASSAVO_PASSWORD (for login flow)
```

### 1.3 client.py - Async API Client
Adapt from PhysicianX `client.py`:
- `ClassavoClient` class with httpx.AsyncClient
- `login()` method → POST /api/login → store token
- `make_request(method, endpoint, data)` → generic HTTP calls
- Rate limiting (reuse pattern from PhysicianX)
- Auto-add `Authorization: Token {token}` header

### 1.4 auth.py - Authentication
- Store token after login
- `verify_token()` → call GET /api/me to validate
- Support both:
  - Pre-configured token via env var
  - Login flow via username/password

### 1.5 main.py - FastMCP Server
```python
from fastmcp import FastMCP
from tools import init_tools

mcp = FastMCP(
    name="Classavo MCP Server",
    instructions="""AI assistant for Classavo education platform.

    Available capabilities:
    1. Authentication - Login, view profile
    2. Courses - List, create, manage courses
    3. Assignments - Create, view, grade assignments
    4. Students - View rosters, track attendance
    5. Submissions - Review and grade student work
    """,
)

init_tools(mcp)

if __name__ == "__main__":
    mcp.run()
```

---

## Phase 2: MCP Tools by User Type (2-3 hours)

### PROFESSOR TOOLS (Primary Focus)

#### 2.1 auth_tools.py - Authentication
| Tool | API Endpoint | Description |
|------|--------------|-------------|
| `login` | POST /api/login | Authenticate with username/password |
| `get_my_profile` | GET /api/me | Get current user info + role |
| `logout` | POST /api/logout | Invalidate token |

#### 2.2 course_tools.py - Course Management
| Tool | API Endpoint | Use Case |
|------|--------------|----------|
| `list_my_courses` | GET /api/v2/courses/ | "Show me my courses" |
| `get_course_details` | GET /api/v2/courses/{id}/ | "Tell me about Chemistry 101" |
| `create_course` | POST /api/v2/courses/ | "Create a new course for Fall 2024" |
| `get_course_roster` | GET /api/v2/courses/{id}/roster/ | "Who's enrolled in my class?" |
| `get_course_analytics` | GET /api/v2/insights/ | "How are my students performing?" |

#### 2.3 content_tools.py - Content & Textbooks
| Tool | API Endpoint | Use Case |
|------|--------------|----------|
| `list_chapters` | GET /api/chapters/ | "Show chapters in this course" |
| `get_chapter_content` | GET /api/file/{id}/ | "Get chapter 3 content" |
| `search_marketplace` | GET /api/marketplace/ | "Find chemistry textbooks" |
| `list_drive_files` | GET /api/v2/drive/ | "Show my uploaded files" |

#### 2.4 assignment_tools.py - Assignments & Quizzes
| Tool | API Endpoint | Use Case |
|------|--------------|----------|
| `list_assignments` | GET /api/assignments/ | "Show all assignments for this course" |
| `get_assignment` | GET /api/assignments/{id}/ | "Get details of homework 5" |
| `create_assignment` | POST /api/assignments/ | "Create a quiz with 10 questions" |
| `get_assignment_stats` | GET /api/assignments/{id}/stats | "How did students do on the midterm?" |

#### 2.5 grading_tools.py - Grading & Submissions
| Tool | API Endpoint | Use Case |
|------|--------------|----------|
| `list_submissions` | GET /api/v2/submissions/ | "Show submissions for homework 3" |
| `get_submission_detail` | GET /api/v2/submissions/{id}/ | "Show John's submission" |
| `grade_submission` | PUT /api/v2/submissions/{id}/grade/ | "Grade this as 85/100" |
| `get_gradebook` | GET /api/v2/gradebook/ | "Show full gradebook for Chemistry" |
| `bulk_grade` | POST /api/v2/gradebook/bulk | "Auto-grade all pending submissions" |

#### 2.6 attendance_tools.py - Attendance Tracking
| Tool | API Endpoint | Use Case |
|------|--------------|----------|
| `start_attendance` | POST /api/v2/attendance/session | "Start attendance for today's class" |
| `get_attendance_code` | GET /api/v2/attendance/code | "What's today's attendance code?" |
| `view_attendance` | GET /api/v2/attendance/ | "Show attendance for this week" |
| `mark_student_present` | POST /api/v2/attendance/ | "Mark John as present" |

#### 2.7 polling_tools.py - Live Polling
| Tool | API Endpoint | Use Case |
|------|--------------|----------|
| `create_poll` | POST /api/v2/polling/ | "Create a poll: What's the pH of water?" |
| `start_poll` | POST /api/v2/polling/{id}/start | "Launch the poll now" |
| `get_poll_results` | GET /api/v2/polling/{id}/results | "Show poll results" |
| `end_poll` | POST /api/v2/polling/{id}/end | "Close the poll" |

#### 2.8 discussion_tools.py - Discussion Boards
| Tool | API Endpoint | Use Case |
|------|--------------|----------|
| `list_discussions` | GET /api/discussions/ | "Show discussion threads" |
| `create_discussion` | POST /api/discussions/ | "Start a discussion about Chapter 5" |
| `get_discussion_comments` | GET /api/discussions/{id}/comments | "Show comments on this thread" |
| `reply_to_discussion` | POST /api/discussions/{id}/comments | "Post instructor reply" |
| `pin_comment` | POST /api/discussions/{id}/pin | "Pin this important answer" |

#### 2.9 playlist_tools.py - Content Playlists
| Tool | API Endpoint | Use Case |
|------|--------------|----------|
| `list_playlists` | GET /api/v2/drive/playlists | "Show my playlists" |
| `create_playlist` | POST /api/v2/drive/playlists | "Create a playlist for Week 1" |
| `add_to_playlist` | POST /api/v2/drive/playlists/{id}/items | "Add chapter 3 to this playlist" |
| `start_presentation` | POST /api/v2/drive/playlists/{id}/present | "Start presenting this playlist" |

#### 2.10 export_tools.py - LMS Integration
| Tool | API Endpoint | Use Case |
|------|--------------|----------|
| `export_to_canvas` | GET /api/v2/gradebook/export/canvas | "Export grades to Canvas" |
| `export_to_blackboard` | GET /api/v2/gradebook/export/blackboard | "Export grades to Blackboard" |
| `export_to_brightspace` | GET /api/v2/gradebook/export/brightspace | "Export to D2L BrightSpace" |

#### 2.11 clone_tools.py - Cloning (Professor)
| Tool | API Endpoint | Use Case |
|------|--------------|----------|
| `clone_course` | POST /api/clone/course | "Clone this course for next semester" |
| `clone_assignment` | POST /api/clone/assignment | "Copy this quiz to another course" |
| `clone_all_assignments` | POST /api/clone/assignments/bulk | "Copy all assignments to new course" |

#### 2.12 search_tools.py - Search
| Tool | API Endpoint | Use Case |
|------|--------------|----------|
| `global_search` | GET /api/v2/search/ | "Search for 'photosynthesis' across all courses" |

### STUDENT TOOLS

#### student_tools.py - Student Experience
| Tool | API Endpoint | Use Case |
|------|--------------|----------|
| `view_my_courses` | GET /api/v2/courses/ | "What courses am I enrolled in?" |
| `view_my_grades` | GET /api/v2/gradebook/student | "What's my grade in Chemistry?" |
| `check_in_attendance` | POST /api/v2/attendance/checkin | "Mark me present with code 1234" |
| `submit_assignment` | POST /api/v2/submissions/ | "Submit my homework" |
| `view_upcoming_deadlines` | GET /api/v2/dashboard/ | "What's due this week?" |
| `vote_in_poll` | POST /api/v2/polling/{id}/vote | "Vote option B" |
| `view_chapter_content` | GET /api/file/{id}/ | "Show me Chapter 3" |
| `join_discussion` | POST /api/discussions/{id}/comments | "Post my comment" |
| `get_notifications` | GET /api/me/notifications | "What's new?" |

---

## Security & Privacy Controls (CRITICAL)

### Data Privacy Rules

| User Type | Can Access | CANNOT Access |
|-----------|------------|---------------|
| **Student** | Own grades only | Other students' grades |
| **Student** | Own submissions | Other students' submissions |
| **Student** | Own attendance | Other students' attendance |
| **Student** | Course roster (names only) | Student emails/contact info |
| **Professor** | All student data in their courses | Students from other courses |

### Implementation Strategy

#### 1. Role-Based Tool Filtering
```python
# In main.py - role-based tool exposure
user_role = await get_user_role(ctx)  # 1=student, 2=professor

STUDENT_TOOLS = [
    "login", "logout", "get_my_profile",
    "view_my_courses", "view_my_grades",  # Only OWN grades
    "view_my_submissions",                 # Only OWN submissions
    "check_in_attendance",                 # Only mark SELF present
    "submit_assignment", "vote_in_poll",
    "view_chapter_content", "join_discussion",
    "get_my_notifications", "view_my_deadlines"
]

PROFESSOR_TOOLS = STUDENT_TOOLS + [
    "get_course_roster", "get_gradebook",  # Can see all students
    "grade_submission", "bulk_grade",
    "view_attendance", "mark_student_present",
    "create_assignment", "create_poll", ...
]

# Filter exposed tools based on role
if user_role == 1:  # Student
    exposed_tools = STUDENT_TOOLS
elif user_role == 2:  # Professor
    exposed_tools = PROFESSOR_TOOLS
```

#### 2. API-Level Protection (Backend handles this)
The Classavo API already enforces permissions:
- `GET /api/v2/gradebook/student` → Returns ONLY logged-in student's grades
- `GET /api/v2/submissions/?student=me` → Returns ONLY own submissions
- Professors use different endpoints with full access

#### 3. MCP Tool Design for Students
```python
@mcp.tool(name="view_my_grades")
async def view_my_grades(course_id: str, ctx: Context = None):
    """View YOUR grades in a course. Students can only see their own grades."""
    client = ClassavoClient.from_context(ctx)
    # API automatically returns only the logged-in user's grades
    return await client.get("/api/v2/gradebook/student", params={"course": course_id})

# NO tool like "view_student_grades(student_id)" for students!
```

#### 4. Safeguards in Tool Descriptions
```python
@mcp.tool(
    name="get_gradebook",
    description="[PROFESSOR ONLY] View all student grades in a course. "
                "Students cannot access this tool.",
    tags={"professor", "grading"}
)
async def get_gradebook(...):
    # Verify user is professor before proceeding
    user = await client.get("/api/me")
    if user.get("role") != 2:
        raise PermissionError("Only professors can view the full gradebook")
    ...
```

### Privacy Checklist

- [ ] Student tools NEVER accept `student_id` parameter (always use logged-in user)
- [ ] Professor-only tools verify role before execution
- [ ] Gradebook/roster tools are professor-only
- [ ] API responses are filtered by Classavo backend (defense in depth)
- [ ] Tool descriptions clearly state access level
- [ ] Error messages don't leak other students' data

---

## Phase 3: Testing & Documentation (1 hour)

### 3.1 Test with Claude Desktop
Add to `~/.config/claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "classavo": {
      "command": "python",
      "args": ["/path/to/classavo-mcp/main.py"],
      "env": {
        "CLASSAVO_API_URL": "https://api.classavo.com",
        "CLASSAVO_USERNAME": "user@example.com",
        "CLASSAVO_PASSWORD": "password"
      }
    }
  }
}
```

### 3.2 README.md
- Installation instructions
- Environment variables
- Available tools
- Example usage

---

## Files to Copy/Adapt from PhysicianX MCP

| PhysicianX File | Classavo Adaptation |
|-----------------|---------------------|
| `main.py` | Change name/instructions, same structure |
| `config.py` | Replace SendGrid vars with Classavo vars |
| `client.py` | Replace SendGrid SDK with httpx calls |
| `auth.py` | Adapt for Django Token auth |
| `tools/__init__.py` | Same pattern, different tool modules |
| `tests/conftest.py` | Reuse mock patterns |

---

## Questions to Ask Classavo Team

Before starting implementation, confirm:

1. **API Base URL**: What's the production API URL?
2. **Authentication**:
   - Do they want login flow (username/password)?
   - Or will they provide a pre-generated API token?
3. **OpenAPI Spec**: Is `/api/v2/docs/` accessible? (Could auto-generate tools)
4. **Priority Features**: Which tools are most important?
   - Courses? Assignments? Grading? Attendance?
5. **User Role**: Will this be used by professors only, or students too?

---

## Deliverables

By end of today:
1. Working MCP server with core tools
2. Login authentication flow
3. Course and assignment management
4. README with setup instructions
5. Claude Desktop configuration example

---

## Dependencies

```txt
# requirements.txt
fastmcp>=2.0.0
httpx>=0.27.0
python-dotenv>=1.0.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

---

## Implementation Order

### Phase 1: Core Infrastructure (1 hour)
1. [x] Create new repo: `classavo-mcp/`
2. [x] Copy patterns from PhysicianX: config.py, client.py structure
3. [x] Implement Classavo-specific auth (Django Token auth)
4. [ ] Test login flow with Classavo API

### Phase 2: Essential Tools (2 hours)
5. [x] auth_tools.py - login, profile, logout
6. [x] course_tools.py - list, get, roster
7. [x] assignment_tools.py - list, get, create
8. [ ] grading_tools.py - submissions, grade
9. [ ] Quick test with Claude Desktop

### Phase 3: Full Professor Suite (1.5 hours)
10. [ ] attendance_tools.py - codes, tracking
11. [ ] polling_tools.py - create, start, results
12. [ ] discussion_tools.py - threads, comments
13. [ ] content_tools.py - chapters, drive files
14. [ ] analytics (gradebook, insights)

### Phase 4: Student Tools (1 hour)
15. [ ] student_tools.py - grades, submissions, deadlines
16. [ ] attendance check-in, poll voting
17. [ ] notifications, discussions

### Phase 5: Polish & Delivery (30 min)
18. [ ] README.md with setup instructions
19. [ ] Claude Desktop config example
20. [ ] Package and deliver

**Total estimated time: 5-6 hours**
