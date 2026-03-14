"""Chapter/Textbook management tools for Classavo MCP Server.

Handles course chapters (interactive textbooks) including content reading and navigation.
"""

import logging
import random
import string
import uuid
from typing import Any, Dict, List, Optional

from fastmcp import Context

from tools import mcp
from auth import get_client

logger = logging.getLogger(__name__)


@mcp.tool(
    name="list_chapters",
    description="List all chapters (textbooks) for a course. "
    "Use the course public_id (e.g., 'W89PCC4'), not the UUID.",
    tags={"chapters", "professor", "student", "content"},
)
async def list_chapters(
    public_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    List all chapters for a course.

    Args:
        public_id: The course public ID (e.g., 'W89PCC4')
        ctx: MCP context for logging

    Returns:
        Dict with list of chapters
    """
    try:
        if ctx:
            await ctx.info(f"Fetching chapters for course {public_id}...")

        client = get_client()
        result = await client.get(f"/api/courses/{public_id}/chapters")

        chapters = result if isinstance(result, list) else result.get("results", [])

        if ctx:
            await ctx.info(f"Found {len(chapters)} chapters")

        return {
            "status": "success",
            "public_id": public_id,
            "count": len(chapters),
            "chapters": chapters,
        }

    except Exception as e:
        error_msg = f"Failed to list chapters: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="get_chapter",
    description="Get detailed information about a chapter including its structure and content. "
    "Use this to read chapter text and summaries.",
    tags={"chapters", "professor", "student", "content"},
)
async def get_chapter(
    chapter_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get chapter details and content.

    Args:
        chapter_id: The chapter UUID/identity
        ctx: MCP context for logging

    Returns:
        Dict with chapter details and content
    """
    try:
        if ctx:
            await ctx.info(f"Fetching chapter {chapter_id}...")

        client = get_client()

        # Get file/chapter details
        chapter_info = await client.get(f"/api/file/{chapter_id}")

        # Get chapter headings (structure/TOC)
        try:
            headings = await client.get(f"/api/chapters/{chapter_id}/headings")
        except Exception:
            headings = []

        if ctx:
            await ctx.info(f"Loaded chapter: {chapter_info.get('title', 'Unknown')}")

        return {
            "status": "success",
            "chapter": chapter_info,
            "headings": headings,
        }

    except Exception as e:
        error_msg = f"Failed to get chapter: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="get_chapter_headings",
    description="Get the table of contents (headings/sections) for a chapter. "
    "Useful for understanding chapter structure before reading specific sections.",
    tags={"chapters", "professor", "student", "content"},
)
async def get_chapter_headings(
    chapter_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get chapter headings/table of contents.

    Args:
        chapter_id: The chapter UUID/identity
        ctx: MCP context for logging

    Returns:
        Dict with chapter headings
    """
    try:
        if ctx:
            await ctx.info(f"Fetching headings for chapter {chapter_id}...")

        client = get_client()
        result = await client.get(f"/api/chapters/{chapter_id}/headings")

        headings = result if isinstance(result, list) else result.get("headings", [])

        if ctx:
            await ctx.info(f"Found {len(headings)} headings")

        return {
            "status": "success",
            "chapter_id": chapter_id,
            "count": len(headings),
            "headings": headings,
        }

    except Exception as e:
        error_msg = f"Failed to get chapter headings: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


def extract_text_from_plate_node(node: dict) -> str:
    """
    Extract text from a single Plate.js node.

    Args:
        node: A Plate.js node dict

    Returns:
        Text content of the node
    """
    if not isinstance(node, dict):
        return ""

    # Skip special node types that don't contain readable text
    node_type = node.get("type", "")
    if node_type in ("classavo_chapter_question",):
        return ""  # Questions are handled separately

    # If it has a 'text' field directly, return it
    if "text" in node:
        return node["text"]

    # Otherwise, recurse into children
    children = node.get("children", [])
    if children:
        child_texts = []
        for child in children:
            if isinstance(child, dict):
                text = extract_text_from_plate_node(child)
                if text:
                    child_texts.append(text)
            elif isinstance(child, str):
                child_texts.append(child)
        return "".join(child_texts)  # Join without newline for inline elements

    return ""


def extract_text_from_plate_content(content: any) -> str:
    """
    Extract plain text from Plate.js JSON content.

    Plate.js stores content as a tree of nodes with 'children' and 'text' fields.
    This recursively extracts all text content, preserving paragraph structure.

    Args:
        content: Plate.js JSON content (list or dict)

    Returns:
        Plain text string with paragraphs separated by newlines
    """
    if content is None:
        return ""

    if isinstance(content, str):
        return content

    if isinstance(content, dict):
        # Handle the root 'content' field if present
        if "content" in content and isinstance(content["content"], list):
            return extract_text_from_plate_content(content["content"])
        return extract_text_from_plate_node(content)

    if isinstance(content, list):
        paragraphs = []
        for item in content:
            if isinstance(item, dict):
                text = extract_text_from_plate_node(item)
                if text.strip():  # Skip empty paragraphs
                    # Add heading markers for better readability
                    node_type = item.get("type", "")
                    if node_type == "h1":
                        text = f"# {text}"
                    elif node_type == "h2":
                        text = f"## {text}"
                    elif node_type == "h3":
                        text = f"### {text}"
                    paragraphs.append(text)
        return "\n\n".join(paragraphs)

    return ""


def extract_questions_from_chapter(data: dict) -> list:
    """
    Extract embedded questions from chapter data.

    Args:
        data: Chapter data containing 'questions' field

    Returns:
        List of question dicts with id, title, and answers
    """
    questions = []
    questions_data = data.get("questions", {})

    # Process both 'create' and 'edit' sections
    for section in ["create", "edit"]:
        section_data = questions_data.get(section, {})
        for q_id, q_data in section_data.items():
            qa_list = q_data.get("questions_and_answers_list", [])
            for qa in qa_list:
                # Extract question title text
                title_content = qa.get("title", [])
                title_text = extract_text_from_plate_content(title_content)

                # Extract answers
                answers = []
                for ans in qa.get("answer", []):
                    ans_title = extract_text_from_plate_content(ans.get("title", []))
                    answers.append({
                        "text": ans_title,
                        "is_correct": ans.get("is_correct", False),
                    })

                questions.append({
                    "identity": qa.get("identity", q_id),
                    "question": title_text,
                    "question_type": q_data.get("question_type"),
                    "points": q_data.get("points"),
                    "answers": answers,
                })

    return questions


@mcp.tool(
    name="get_chapter_content",
    description="Get the full text content of a chapter for reading or summarization. "
    "Returns the chapter body text that can be used for AI analysis.",
    tags={"chapters", "professor", "student", "content", "read"},
)
async def get_chapter_content(
    chapter_id: str,
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Get chapter text content.

    Args:
        chapter_id: The chapter UUID/identity
        ctx: MCP context for logging

    Returns:
        Dict with chapter content including extracted plain text
    """
    try:
        if ctx:
            await ctx.info(f"Fetching content for chapter {chapter_id}...")

        client = get_client()

        # Get chapter/file details - content is in 'content' field as Plate.js JSON
        chapter_info = await client.get(f"/api/file/{chapter_id}")

        title = chapter_info.get("title", "")
        raw_content = chapter_info.get("content")  # Plate.js JSON content

        # Extract plain text from Plate.js content
        plain_text = ""
        if isinstance(raw_content, dict):
            # Content field contains 'content' array and 'questions' object
            content_array = raw_content.get("content", [])
            plain_text = extract_text_from_plate_content(content_array)
        elif isinstance(raw_content, list):
            plain_text = extract_text_from_plate_content(raw_content)

        # Extract embedded questions
        embedded_questions = []
        if isinstance(raw_content, dict):
            embedded_questions = extract_questions_from_chapter(raw_content)

        if ctx:
            if plain_text:
                await ctx.info(f"Loaded chapter: {len(plain_text)} chars, {len(embedded_questions)} questions")
            else:
                await ctx.info("Chapter loaded but content may be empty")

        return {
            "status": "success",
            "chapter_id": chapter_id,
            "title": title,
            "text": plain_text,  # Plain text for easy reading/summarization
            "embedded_questions": embedded_questions,  # Questions embedded in the chapter
        }

    except Exception as e:
        error_msg = f"Failed to get chapter content: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


def generate_question_id() -> str:
    """Generate a UUID for a new question."""
    return str(uuid.uuid4())


def generate_node_id() -> str:
    """Generate a short ID for Plate.js nodes."""
    return ''.join(random.choices(string.ascii_letters + string.digits + '_-', k=10))


def create_plate_text(text: str) -> list:
    """Create a Plate.js paragraph with text."""
    return [{"type": "p", "children": [{"text": text}], "id": generate_node_id()}]


def create_mcq_question_data(
    question_text: str,
    options: list,
    correct_index: int,
    points: str = "1.0",
    points_participation: str = "0.5",
) -> tuple:
    """
    Create MCQ question data for embedding in a chapter.

    Args:
        question_text: The question text
        options: List of answer option strings
        correct_index: Index of the correct answer (0-based)
        points: Points for correct answer
        points_participation: Participation points

    Returns:
        Tuple of (question_id, question_node, question_data)
    """
    question_id = generate_question_id()

    # Create the content node that embeds the question
    question_node = {
        "type": "classavo_chapter_question",
        "question_id": question_id,
        "children": [{"text": ""}],
        "id": generate_node_id(),
    }

    # Create answer objects
    answers = []
    for i, option_text in enumerate(options):
        answers.append({
            "identity": generate_question_id(),
            "title": create_plate_text(option_text),
            "is_correct": i == correct_index,
            "index": i,
        })

    # Create the question data for the questions.create section
    question_data = {
        "questions_and_answers_list": [{
            "identity": f"new---{random.random()}",
            "title": create_plate_text(question_text),
            "answer": answers,
        }],
        "question_type": 1,  # 1 = multiple choice
        "points": points,
        "points_participation": points_participation,
        "points_multiple_correct_policy": 5,
        "is_extra_credit": False,
        "max_attempts": 1,
        "message_if_correct": "",
        "message_if_incorrect": "",
        "use_ai_message": False,
        "feedback_type": 1,
        "feedback_timing": 1,
        "feedback_delay_days": 0,
        "identity": question_id,
    }

    return question_id, question_node, question_data




@mcp.tool(
    name="add_chapter_question",
    description="[PROFESSOR ONLY] Add a multiple choice question to a chapter. "
    "The question will be embedded directly in the chapter content. "
    "Options should be comma-separated, and correct_option_index is 0-based (0 for first option).",
    tags={"chapters", "professor", "questions", "content"},
)
async def add_chapter_question(
    chapter_id: str,
    question_text: str,
    options: str,
    correct_option_index: int,
    points: str = "1.0",
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Add a multiple choice question to a chapter.

    Args:
        chapter_id: The chapter UUID/identity
        question_text: The question text
        options: Comma-separated answer options (e.g., "Option A, Option B, Option C, Option D")
        correct_option_index: Index of correct answer (0-based, e.g., 0 for first option)
        points: Points for the question (default "1.0")
        ctx: MCP context for logging

    Returns:
        Dict with created question info
    """
    try:
        if ctx:
            await ctx.info(f"Adding question to chapter {chapter_id}...")

        client = get_client()

        # Get current chapter content
        chapter_info = await client.get(f"/api/file/{chapter_id}")
        raw_content = chapter_info.get("content", {})

        # Ensure content structure exists
        if not isinstance(raw_content, dict):
            raw_content = {"content": [], "questions": {"create": {}, "edit": {}, "delete": []}}

        content_array = raw_content.get("content", [])
        questions_obj = raw_content.get("questions", {"create": {}, "edit": {}, "delete": []})

        if "create" not in questions_obj:
            questions_obj["create"] = {}
        if "edit" not in questions_obj:
            questions_obj["edit"] = {}
        if "delete" not in questions_obj:
            questions_obj["delete"] = []

        # Parse options
        option_list = [opt.strip() for opt in options.split(",")]
        if len(option_list) < 2:
            raise ValueError("At least 2 options are required")
        if correct_option_index < 0 or correct_option_index >= len(option_list):
            raise ValueError(f"correct_option_index must be between 0 and {len(option_list) - 1}")

        # Create the question
        question_id, question_node, question_data = create_mcq_question_data(
            question_text=question_text,
            options=option_list,
            correct_index=correct_option_index,
            points=points,
        )

        # Add question node to content (before the last empty paragraph if exists)
        # Also add an empty paragraph after the question
        empty_para = {"type": "p", "id": generate_node_id(), "children": [{"text": ""}]}
        content_array.append(question_node)
        content_array.append(empty_para)

        # Add question data to questions.create
        questions_obj["create"][question_id] = question_data

        # Update the chapter
        updated_content = {
            "content": content_array,
            "questions": questions_obj,
        }

        result = await client.put(
            f"/api/file/{chapter_id}",
            data={"content": updated_content},
        )

        if ctx:
            await ctx.info(f"Question added successfully!")

        return {
            "status": "success",
            "message": "Question added to chapter",
            "chapter_id": chapter_id,
            "question_id": question_id,
            "question_text": question_text,
            "options": option_list,
            "correct_option": option_list[correct_option_index],
        }

    except Exception as e:
        error_msg = f"Failed to add chapter question: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)


@mcp.tool(
    name="add_multiple_chapter_questions",
    description="[PROFESSOR ONLY] Add multiple MCQ questions to a chapter at once. "
    "Each question should be a JSON object with: question_text, options (array), correct_option_index. "
    "Example: [{\"question_text\": \"What is X?\", \"options\": [\"A\", \"B\", \"C\"], \"correct_option_index\": 0}]",
    tags={"chapters", "professor", "questions", "content"},
)
async def add_multiple_chapter_questions(
    chapter_id: str,
    questions_json: str,
    points_per_question: str = "1.0",
    ctx: Context = None,
) -> Dict[str, Any]:
    """
    Add multiple MCQ questions to a chapter.

    Args:
        chapter_id: The chapter UUID/identity
        questions_json: JSON array of questions, each with question_text, options, correct_option_index
        points_per_question: Points for each question (default "1.0")
        ctx: MCP context for logging

    Returns:
        Dict with created questions info
    """
    import json

    try:
        if ctx:
            await ctx.info(f"Adding multiple questions to chapter {chapter_id}...")

        # Parse questions JSON
        try:
            questions_list = json.loads(questions_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        if not isinstance(questions_list, list):
            raise ValueError("questions_json must be a JSON array")

        client = get_client()

        # Get current chapter content
        chapter_info = await client.get(f"/api/file/{chapter_id}")
        raw_content = chapter_info.get("content", {})

        # Ensure content structure exists
        if not isinstance(raw_content, dict):
            raw_content = {"content": [], "questions": {"create": {}, "edit": {}, "delete": []}}

        content_array = raw_content.get("content", [])
        questions_obj = raw_content.get("questions", {"create": {}, "edit": {}, "delete": []})

        if "create" not in questions_obj:
            questions_obj["create"] = {}
        if "edit" not in questions_obj:
            questions_obj["edit"] = {}
        if "delete" not in questions_obj:
            questions_obj["delete"] = []

        added_questions = []

        for q in questions_list:
            question_text = q.get("question_text", "")
            options = q.get("options", [])
            correct_index = q.get("correct_option_index", 0)

            if not question_text or len(options) < 2:
                continue

            # Create the question
            question_id, question_node, question_data = create_mcq_question_data(
                question_text=question_text,
                options=options,
                correct_index=correct_index,
                points=points_per_question,
            )

            # Add question node to content
            empty_para = {"type": "p", "id": generate_node_id(), "children": [{"text": ""}]}
            content_array.append(question_node)
            content_array.append(empty_para)

            # Add question data to questions.create
            questions_obj["create"][question_id] = question_data

            added_questions.append({
                "question_id": question_id,
                "question_text": question_text,
                "correct_answer": options[correct_index] if correct_index < len(options) else None,
            })

        # Update the chapter
        updated_content = {
            "content": content_array,
            "questions": questions_obj,
        }

        result = await client.put(
            f"/api/file/{chapter_id}",
            data={"content": updated_content},
        )

        if ctx:
            await ctx.info(f"Added {len(added_questions)} questions successfully!")

        return {
            "status": "success",
            "message": f"Added {len(added_questions)} questions to chapter",
            "chapter_id": chapter_id,
            "questions_added": added_questions,
        }

    except Exception as e:
        error_msg = f"Failed to add chapter questions: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        logger.error(error_msg)
        raise RuntimeError(error_msg)
